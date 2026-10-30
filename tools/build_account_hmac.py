"""Compile a narrow account-only software HMAC bridge against original ABI."""
from pathlib import Path
import subprocess,json,hashlib
r=Path('/mnt/c/SHENG_WORKSPACE')
sdk=Path('/root/hmos-work/sdk-6.0.0.47/installed/native')
src=Path('/root/hmos-work/graphics-deps/source/security_huks')
d=r/'compat/sheng-framework/account-hmac-v1';link=r/'work/donor-hdi-link'
report={'scope':'account file HMAC only, no TEE or authentication implementation','donor':{},'upstream':{}}
for name in ['libaccountmgr.z.so','libhukssdk.z.so','libcrypto_openssl.z.so']:
    report['donor'][name]=hashlib.sha256((link/name).read_bytes()).hexdigest()
for repo in [src,src.parent/'account_os_account']:
    report['upstream'][repo.name]=subprocess.check_output(['git','-C',str(repo),'rev-parse','HEAD'],text=True).strip()
flags=[str(sdk/'llvm/bin/clang'),'--target=aarch64-linux-ohos','-std=gnu11','-O2','-Wall','-Wextra','-Werror','-Wno-misleading-indentation','-I'+str(src/'interfaces/inner_api/huks_standard/main/include'),str(d/'account_hmac.c')]
crypto=[str(link/'libcrypto_openssl.z.so'),'-Wl,--allow-shlib-undefined']
(d/'exports.map').write_text('1.0 { global: HksKeyExist; HksGenerateKey; HksInit; HksUpdate; HksFinish; HksAbort; local: *; };\n')
subprocess.run(flags+['-shared','-fPIC','-Wl,-z,relro,-z,now','-Wl,--version-script='+str(d/'exports.map')]+crypto+['-o',str(d/'libsheng_account_hmac.so')],check=True)
subprocess.run(flags+['-DCONTRACT_MAIN',str(link/'libhukssdk.z.so')]+crypto+['-o',str(d/'account_hmac_contract')],check=True)
for name in ['libsheng_account_hmac.so','account_hmac_contract']:
    subprocess.run([str(sdk/'llvm/bin/llvm-strip'),str(d/name)],check=True)
    report[name]={'sha256':hashlib.sha256((d/name).read_bytes()).hexdigest(),'bytes':(d/name).stat().st_size}
(d/'manifest.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))
