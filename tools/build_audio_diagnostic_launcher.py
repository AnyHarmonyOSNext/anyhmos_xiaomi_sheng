from pathlib import Path
import subprocess,hashlib
r=Path(__file__).resolve().parent.parent
sdk=Path('/root/hmos-work/sdk-6.0.0.47/installed/native')
p=r/'compat/debug-tools/native_audio_diagnostic_launcher'
subprocess.run([str(sdk/'llvm/bin/clang++'),'--target=aarch64-linux-ohos','-O2','-Wall','-Wextra','-Werror',str(r/'tools/native_audio_diagnostic_launcher.cpp'),'-ldl','-o',str(p)],check=True)
print(p.stat().st_size,hashlib.sha256(p.read_bytes()).hexdigest())
