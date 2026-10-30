"""Expose the software 4.0 backend through the donor's inherited 4.1 ABI.

Only inherited operations are forwarded. Unsupported 4.1 extended authentication
operations return failure; this never fabricates successful authentication.
"""
from pathlib import Path
import subprocess,urllib.request,shutil,re,json,hashlib,gzip,tarfile
r=Path('/mnt/c/SHENG_WORKSPACE')
d=Path('/root/hmos-work/sheng-useriam-port');src=Path('/root/hmos-work/graphics-deps/source')
sdk=Path('/root/hmos-work/sdk-6.0.0.47/installed/native')
commit='74caef74888bc73eecd3719e59f09b7e4b4e9d6f'
idl=d/'idl';(idl/'user_auth/v4_1').mkdir(parents=True,exist_ok=True)
if not (idl/'user_auth/v4_0').exists():shutil.copytree(src/'drivers_interface/user_auth/v4_0',idl/'user_auth/v4_0')
for name in ['IUserAuthInterface.idl','UserAuthTypes.idl']:
 p=idl/'user_auth/v4_1'/name
 if not p.exists():p.write_bytes(urllib.request.urlopen(f'https://raw.githubusercontent.com/openharmony/drivers_interface/{commit}/user_auth/v4_1/{name}',timeout=30).read())
gen=d/'generated41';gen.mkdir(exist_ok=True)
for name in ['UserAuthTypes.idl','IUserAuthInterface.idl']:
 subprocess.run(['/root/hmos-work/graphics-deps/hdi-gen','-m','ipc','-l','cpp','-r','ohos.hdi:'+str(idl),'-c',str(idl/'user_auth/v4_1'/name),'-d',str(gen)],check=True)
header=gen/'user_auth/v4_1/user_auth_interface_service.h'
text=header.read_text()
methods=re.findall(r'int32_t\s+(\w+)\((.*?)\)\s+override;',text,re.S)
assert len(methods)>30 and {name for name,_ in methods}>={'GetCredential','BeginAuthenticationExt','BeginEnrollmentExt'}
code='''// Private sheng adaptation; generated signatures from pinned OpenHarmony IDL.
// AnyHarmonyOS software backend retains its upstream Apache-2.0 license.
#include "user_auth/v4_1/iuser_auth_interface.h"
#include <dlfcn.h>
#include <new>
using namespace OHOS;
using Base=HDI::UserAuth::V4_0::IUserAuthInterface;
class ShengUserAuth41 final : public HDI::UserAuth::V4_1::IUserAuthInterface {
 sptr<Base> base_;
public:
 explicit ShengUserAuth41(Base *base):base_(base){}
'''
for name,args in methods:
 args=' '.join(args.split())
 # Generated parameter types use vectors and references, without nested commas.
 params=[a.strip() for a in args.split(',') if a.strip()]
 names=[re.search(r'(\w+)$',p).group(1) for p in params]
 body='return base_->'+name+'('+','.join(names)+');'
 if name in ['BeginAuthenticationExt','BeginEnrollmentExt']:
  body=''.join('(void)'+n+';' for n in names)+'return -8;'
 code+=' int32_t '+name+'('+args+') override {'+body+'}\n'
code+='''};
extern "C" HDI::UserAuth::V4_1::IUserAuthInterface *UserAuthInterfaceImplGetInstance(){
 static void *lib=dlopen("/compat/lib64/libsheng_userauth_4_0.so",RTLD_NOW|RTLD_LOCAL);
 if(!lib)return nullptr;
 auto factory=reinterpret_cast<Base*(*)()>(dlsym(lib,"UserAuthInterfaceImplGetInstance"));
 if(!factory)return nullptr;
 Base *base=factory();if(!base)return nullptr;
 return new(std::nothrow) ShengUserAuth41(base);
}
'''
(d/'adapter41.cpp').write_text(code)
commands=json.loads((d/'out/build-commands.json').read_text())
cmd=commands[-1];start=cmd.index('-shared')
flags=cmd[1:start]
flags += ['-I'+str(gen),'-I'+str(gen/'user_auth'),'-Wno-unused-parameter']
link=r/'work/donor-hdi-link'
out=d/'out/libuser_auth_interface_service_4.1.z.so'
subprocess.run([str(sdk/'llvm/bin/clang++'),*flags,'-shared','-Wl,-z,defs','-Wl,-soname,'+out.name,str(d/'adapter41.cpp'),str(link/'libc++.so'),str(link/'libutils.z.so'),'-ldl','-o',str(out)],check=True)
with tarfile.open(r/'work/useriam-driver-link.tar.gz') as tar:
 for item in tar.getmembers():
  assert item.isfile() and '..' not in Path(item.name).parts and not item.name.startswith('/')
  p=d/'donor'/item.name;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(tar.extractfile(item).read())
hdf=src/'drivers_hdf_core'
flags += ['-I'+str(p) for p in sorted({p.parent for p in (hdf/'interfaces/inner_api').rglob('*.h')}) if 'khdf' not in str(p)]
for name in ['hdf_device_desc.h','hdf_sbuf_ipc.h','hdf_object_manager.h','hdf_device_section.h']:
 parents={str(p.parent) for p in hdf.rglob(name)}
 flags += ['-I'+p for p in parents]
libs=[str(link/name) for name in ['libc++.so','libutils.z.so','libhilog.so','libhdf_utils.z.so','libhdi.z.so','libipc_single.z.so']]
libs += [str(d/'donor/vendor/lib64'/name) for name in ['libuser_auth_stub_4.0.z.so','libuser_auth_stub_4.1.z.so']]
libs += [str(d/'donor/system/lib64/chipset-sdk-sp/libhdf_host.z.so')]
ipc_adapter=d/'donor/system/lib64/chipset-sdk-sp/libhdf_ipc_adapter.z.so'
ipc_adapter.write_bytes(gzip.decompress((r/'work/libhdf_ipc_adapter.z.so.gz').read_bytes()))
libs += [str(ipc_adapter)]
driver=(src/'drivers_peripheral/user_auth/hdi_service/service/user_auth_interface_driver.cpp').read_text()
driver=driver.replace('#include "v4_0/user_auth_interface_service.h"','#include "user_auth/v4_1/iuser_auth_interface.h"\nextern "C" OHOS::HDI::UserAuth::V4_1::IUserAuthInterface *UserAuthInterfaceImplGetInstance();')
driver=driver.replace('#include "v4_0/user_auth_interface_stub.h"','#include "user_auth/v4_1/user_auth_interface_stub.h"')
driver=driver.replace('#include "user_auth_hdi.h"','').replace('#include "useriam_common.h"','')
driver=driver.replace('using UserAuthInterfaceService = OHOS::HDI::UserAuth::V4_0::UserAuthInterfaceService;','')
driver=driver.replace('using IUserAuthInterface = OHOS::HDI::UserAuth::V4_0::IUserAuthInterface;','using IUserAuthInterface = OHOS::HDI::UserAuth::V4_1::IUserAuthInterface;')
driver=driver.replace('OHOS::sptr<UserAuthInterfaceService> serviceImpl(new (std::nothrow) UserAuthInterfaceService());','OHOS::sptr<IUserAuthInterface> serviceImpl(UserAuthInterfaceImplGetInstance());')
driver=driver.replace('    OHOS::UserIam::Common::Init();','')
(d/'driver41.cpp').write_text(driver)
driver_out=d/'out/libsheng_user_auth_driver.so'
subprocess.run([str(sdk/'llvm/bin/clang++'),*flags,'-D__USER__','-shared','-Wl,-z,defs','-Wl,-soname,'+driver_out.name,str(d/'driver41.cpp'),str(out),*libs,'-ldl','-o',str(driver_out)],check=True)
contract=d/'out/useriam_empty_contract'
subprocess.run([str(sdk/'llvm/bin/clang++'),*flags,str(r/'tools/useriam_empty_contract.cpp'),*libs,str(d/'donor/system/lib64/libuser_auth_proxy_4.0.z.so'),str(d/'donor/system/lib64/libuser_auth_proxy_4.1.z.so'),'-Wl,--allow-shlib-undefined','-ldl','-o',str(contract)],check=True)
dest=r/'compat/sheng-framework/useriam-v1';dest.mkdir(exist_ok=True)
report={'interface_commit':commit,'extended_operations':'unsupported, failure -8','artifacts':{}}
for source,name in [(d/'out/libuser_auth_interface_service_4.0.z.so','libsheng_userauth_4_0.so'),(out,out.name),(driver_out,driver_out.name),(contract,contract.name)]:
 target=dest/name;shutil.copy2(source,target)
 subprocess.run([str(sdk/'llvm/bin/llvm-strip'),str(target)],check=True)
 data=target.read_bytes();(dest/(name+'.gz')).write_bytes(gzip.compress(data,mtime=0))
 report['artifacts'][name]={'bytes':len(data),'gzip_bytes':(dest/(name+'.gz')).stat().st_size,'sha256':hashlib.sha256(data).hexdigest()}
(dest/'manifest.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps(report))
