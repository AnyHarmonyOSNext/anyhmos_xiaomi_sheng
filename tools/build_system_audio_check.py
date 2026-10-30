from pathlib import Path
import subprocess,hashlib
r=Path(__file__).resolve().parent.parent
sdk=Path('/root/hmos-work/sdk-6.0.0.47/installed/native')
p=r/'compat/debug-tools/native_system_audio_check'
subprocess.run([str(sdk/'llvm/bin/clang'),'--target=aarch64-linux-ohos','-O2','-Wall','-Wextra','-Werror','-Wno-deprecated-declarations',str(r/'tools/native_system_audio_check.c'),'-lohaudio','-lm','-o',str(p)],check=True)
print(p.stat().st_size,hashlib.sha256(p.read_bytes()).hexdigest())
