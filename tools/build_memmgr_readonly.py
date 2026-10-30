from pathlib import Path
import subprocess
r = Path('/mnt/c/SHENG_WORKSPACE')
sdk = Path('/root/hmos-work/sdk-6.0.0.47/installed/native')
out = r / 'compat/debug-tools/native_memmgr_readonly'
subprocess.run([str(sdk/'llvm/bin/clang'), '--target=aarch64-linux-ohos', '-O2', '-std=gnu11',
                '-Wall', '-Wextra', '-Werror', str(r/'tools/native_memmgr_readonly.c'), '-o', str(out)], check=True)
subprocess.run([str(sdk/'llvm/bin/llvm-strip'), str(out)], check=True)
print(out.stat().st_size)
