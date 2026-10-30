from pathlib import Path
import subprocess
r=Path('/mnt/c/SHENG_WORKSPACE')
sdk=Path('/root/hmos-work/sdk-6.0.0.47/installed/native')
p=r/'compat/debug-tools/hardware_observe'
subprocess.run([str(sdk/'llvm/bin/clang'),'--target=aarch64-linux-ohos','-O2','-Wall','-Wextra','-Werror',str(r/'tools/hardware_observe.c'),'-o',str(p)],check=True)
subprocess.run([str(sdk/'llvm/bin/llvm-strip'),str(p)],check=True)
print(p.stat().st_size)
