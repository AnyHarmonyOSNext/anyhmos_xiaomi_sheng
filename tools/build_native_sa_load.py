from pathlib import Path
import json
import subprocess

r = Path(__file__).resolve().parent.parent
sdk = Path(json.loads(Path('/root/hmos-work/sdk-6.0.0.47/installation.json').read_text())['sdk'])
subprocess.run([str(sdk/'llvm/bin/clang++'), '--target=aarch64-linux-ohos', '-std=c++17',
                '-Os', '-Wall', '-Wextra', '-Werror', '-fno-exceptions', '-fno-rtti',
                '-nostdlib++', '-include',
                '/root/hmos-work/graphics-deps/sheng-graphics-port/tests/platform_cpp_config.h',
                str(r/'tools/native_sa_load.cpp'),
                str(r/'work/hmos_system/system/system/lib64/chipset-sdk-sp/libc++.so'),
                '-o', str(r/'compat/debug-tools/native_sa_load')], check=True)
