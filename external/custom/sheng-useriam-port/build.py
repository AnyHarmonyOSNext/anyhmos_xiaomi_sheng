from pathlib import Path
import subprocess,re,json,hashlib,os
B=Path(__file__).resolve().parent;R=B.parents[1];S=Path(os.environ['ANYHARMONYOS_OHOS_SOURCE']);A=S/'drivers_peripheral/user_auth/hdi_service';SDK=Path(os.environ['ANYHARMONYOS_SDK']);O=B/'out';O.mkdir(exist_ok=True)
INCS=[Path(os.environ['ANYHARMONYOS_OPENSSL_INCLUDE']),B/'generated',B/'generated/user_auth',A/'interface',A/'adaptor/inc',A/'coauth/inc',A/'common/inc',A/'database/inc',A/'idm/inc',A/'key_mgr/inc',A/'user_auth/inc',A/'utils/inc',A/'service',A.parent/'common/logs',A.parent/'common/utils',S/'bounds_checking_function/include',S/'hiviewdfx_hilog/interfaces/native/innerkits/include',S/'commonlibrary_c_utils/base/include',S/'communication_ipc/interfaces/innerkits/ipc_core/include',S/'drivers_hdf_core/interfaces/inner_api/utils',S/'drivers_hdf_core/interfaces/inner_api/hdi',S/'drivers_hdf_core/interfaces/inner_api/hdi/base',S/'drivers_hdf_core/interfaces/inner_api/host/shared']
INCS += [S/'drivers_hdf_core/interfaces/inner_api/ipc',S/'drivers_hdf_core/interfaces/inner_api/osal/uhdf',S/'drivers_hdf_core/interfaces/inner_api/osal/shared']
COMMON=['--target=aarch64-linux-ohos','-O2','-g','-fPIC','-Wall','-Wextra','-Wno-unused-parameter','-Wno-deprecated-declarations']+['-I'+str(x) for x in INCS]
CPP=['-fno-rtti','-std=c++17','-nostdlib++','-include','/root/hmos-work/graphics-deps/sheng-graphics-port/tests/platform_cpp_config.h']
LIB=Path(os.environ['ANYHARMONYOS_ROM_SYSTEM_LIBS'])
sources=re.findall(r'"([^"\n]+\.(?:c|cpp))"',(A/'BUILD.gn').read_text().split('external_deps')[0]);objects=[];commands=[]
for source in sources:
 p=B/'user_auth_interface_service.cpp' if source=='service/user_auth_interface_service.cpp' else A/source
 o=O/(source.replace('/','_')+'.o');objects.append(o)
 cmd=[str(SDK/'llvm/bin'/('clang++' if p.suffix=='.cpp' else 'clang'))]+COMMON+(CPP if p.suffix=='.cpp' else ['-std=gnu11'])+['-c',str(p),'-o',str(o)];commands.append(cmd)
 if not o.exists() or o.stat().st_mtime<max(p.stat().st_mtime,Path(__file__).stat().st_mtime):subprocess.run(cmd,check=True)
libs=[LIB/n for n in ['libc++.so','libutils.z.so','libhilog.so','libhdf_utils.z.so','libhdi.z.so','libipc_single.z.so','libcrypto_openssl.z.so','libsec_shared.z.so']]
# Use the ROM's original IPC marshalling implementation after separate ABI auditing.
libs.append(Path(os.environ['ANYHARMONYOS_ROM_VENDOR_LIBS'])/'libuser_auth_stub_4.0.z.so')
out=O/'libuser_auth_interface_service_4.0.z.so'
cmd=[str(SDK/'llvm/bin/clang++')]+COMMON+CPP+['-shared','-Wl,-z,defs','-Wl,-soname,'+out.name]+[str(p) for p in objects+libs]+['-o',str(out)];commands.append(cmd);subprocess.run(cmd,check=True)
(O/'build-commands.json').write_text(json.dumps(commands,indent=2)+'\n');print(out,hashlib.sha256(out.read_bytes()).hexdigest())

cmd=[str(SDK/'llvm/bin/clang++')]+COMMON+CPP+[str(B/'contract.cpp'),str(out)]+[str(p) for p in libs]+['-ldl','-Wl,--allow-shlib-undefined','-o',str(O/'useriam_contract')]
subprocess.run(cmd,check=True)

cmd=[str(SDK/'llvm/bin/clang++')]+COMMON+CPP+['-DUSERIAM_WIRE',str(B/'contract.cpp'),str(out)]+[str(p) for p in libs]+[str(LIB/'libuser_auth_proxy_4.0.z.so'),'-ldl','-Wl,--allow-shlib-undefined','-o',str(O/'useriam_wire_contract')]
subprocess.run(cmd,check=True)
