from pathlib import Path
import subprocess,hashlib
r=Path(__file__).resolve().parent.parent
sdk=Path('/root/hmos-work/sdk-6.0.0.47/installed/native')
h=Path('/root/hmos-work/graphics-deps/source/drivers_hdf_core')
p=r/'compat/debug-tools/native_audio_hdi_publisher'
cmd=[str(sdk/'llvm/bin/clang'),'--target=aarch64-linux-ohos','-O2','-Wall','-Wextra','-Werror']
for inc in ['interfaces/inner_api/ipc','interfaces/inner_api/core','interfaces/inner_api/utils','interfaces/inner_api/osal/uhdf']:
 cmd+=['-I'+str(h/inc)]
subprocess.run(cmd+[str(r/'tools/native_audio_hdi_publisher.c'),'-ldl','-o',str(p)],check=True)
print(p.stat().st_size,hashlib.sha256(p.read_bytes()).hexdigest())
p=r/'compat/debug-tools/native_audio_service_launcher'
subprocess.run(cmd[:8]+[str(r/'tools/native_audio_service_launcher.c'),'-o',str(p)],check=True)
print(p.stat().st_size,hashlib.sha256(p.read_bytes()).hexdigest())
