from pathlib import Path
import json
import subprocess

sdk = json.loads(Path('/root/hmos-work/sdk-6.0.0.47/installation.json').read_text())['sdk']
r = Path('/mnt/c/SHENG_WORKSPACE')
subprocess.run([sdk+'/llvm/bin/clang++', '--target=aarch64-linux-ohos', '-std=c++17', '-Os',
                '-Wall', '-Wextra', '-Werror', '-fno-exceptions', '-fno-rtti', '-nostdlib++',
                '-include', '/root/hmos-work/graphics-deps/sheng-graphics-port/tests/platform_cpp_config.h',
                str(r/'tools/native_sa_check.cpp'),
                str(r/'work/hmos_system/system/system/lib64/chipset-sdk-sp/libc++.so'),
                '-o', str(r/'compat/debug-tools/native_sa_check')], check=True)
subprocess.run([sdk+'/llvm/bin/llvm-strip', str(r/'compat/debug-tools/native_sa_check')], check=True)
print((r/'compat/debug-tools/native_sa_check').stat().st_size)
