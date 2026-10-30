"""Build the isolated PAL bridge with original303 Bionic imports (WSL)."""
from pathlib import Path
import hashlib
import json
import subprocess

r=Path(__file__).resolve().parent.parent
sdk=Path('/root/hmos-work/sdk-6.0.0.47/installed/native')
d=r/'compat/sheng-audio/pal-bridge-v1'
cmd=[str(sdk/'llvm/bin/clang'),'--target=aarch64-linux-android33',
     '--sysroot='+str(sdk/'sysroot'),'-isystem',str(sdk/'sysroot/usr/include/aarch64-linux-ohos'),
     '-I/root/hmos-reference/pal-sm8550-a13/inc','-fuse-ld=lld','-fPIC','-shared','-nostdlib',
     '-D_GNU_SOURCE','-mno-outline-atomics','-Wall','-Wextra','-Werror','-O2','-Wl,-z,defs',
     '-Wl,-soname,libsheng_pal_server.so','-L'+str(r/'work/audio-bionic-v1/lib64'),
     str(d/'pal_server.c'),'-lc','-ldl','-o',str(d/'libsheng_pal_server.so')]
subprocess.run(cmd,check=True)
p=d/'libsheng_pal_server.so'
manifest={'command':cmd,'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()}
(r/'analysis/pal-bridge-v1-build.json').write_text(json.dumps(manifest,indent=2)+'\n')
print(json.dumps({k:v for k,v in manifest.items() if k!='command'}))
out=r/'compat/debug-tools/native_pal_bridge_check'
subprocess.run([str(sdk/'llvm/bin/clang'),'--target=aarch64-linux-ohos','-D_GNU_SOURCE',
                '-O2','-Wall','-Wextra','-Werror','-I'+str(d),
                str(r/'tools/native_pal_bridge_check.c'),str(d/'pal_client.c'),'-o',str(out)],check=True)
print('Native client SHA256',hashlib.sha256(out.read_bytes()).hexdigest())
subprocess.run([str(sdk/'llvm/bin/clang'),'--target=aarch64-linux-ohos','-D_GNU_SOURCE',
                '-O2','-Wall','-Wextra','-Werror','-fPIC','-shared','-I'+str(d),'-I'+str(d/'include'),
                str(d/'audio_vdi.c'),str(d/'pal_client.c'),'-pthread','-Wl,-z,defs',
                '-Wl,-soname,libsheng_audio_vdi.so','-o',str(d/'libsheng_audio_vdi.so')],check=True)
subprocess.run([str(sdk/'llvm/bin/clang'),'--target=aarch64-linux-ohos','-O2',
                '-Wall','-Wextra','-Werror','-fPIC','-shared',str(d/'audio_vdi_loader.c'),'-ldl',
                '-Wl,-z,defs','-o',str(d/'libsheng_audio_vdi_loader.so')],check=True)
print('Native VDI and exact-path loader built')
subprocess.run([str(sdk/'llvm/bin/clang'),'--target=aarch64-linux-ohos','-O2',
                '-Wall','-Wextra','-Werror','-fPIC','-shared',str(d/'audio_manager_service.c'),
                '-ldl','-pthread','-Wl,-z,defs','-o',str(d/'libsheng_audio_manager_service.so')],check=True)
subprocess.run([str(sdk/'llvm/bin/clang'),'--target=aarch64-linux-ohos','-D_GNU_SOURCE',
                '-O2','-Wall','-Wextra','-Werror','-I'+str(d/'include'),
                str(r/'tools/native_audio_vdi_check.c'),'-ldl',
                '-o',str(r/'compat/debug-tools/native_audio_vdi_check')],check=True)
