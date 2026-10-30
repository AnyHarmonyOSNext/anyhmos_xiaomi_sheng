from pathlib import Path
import subprocess, hashlib, json
r = Path('/mnt/c/SHENG_WORKSPACE')
sdk = Path('/root/hmos-work/sdk-6.0.0.47/installed/native')
out = r / 'compat/sheng-graphics/surface-diagnostic-v4'
out.mkdir(exist_ok=True)
lib = out / 'libsheng_surface_diagnostic.so'
subprocess.run([str(sdk / 'llvm/bin/clang++'), '--target=aarch64-linux-ohos',
    '-std=c++17', '-O2', '-Wall', '-Wextra', '-Werror', '-fno-exceptions',
    '-fno-rtti', '-nostdlib++', '-shared', '-fPIC', '-include',
    '/root/hmos-work/graphics-deps/sheng-graphics-port/tests/platform_cpp_config.h',
    str(r / 'tools/native_surface_diagnostic_v4.cpp'),
    str(r / 'tools/native_buffer_import_observer.S'),
    str(r / 'work/donor-hdi-link/libc++.so'), '-o', str(lib)], check=True)
subprocess.run([str(sdk / 'llvm/bin/llvm-strip'), str(lib)], check=True)
print(json.dumps(dict(bytes=lib.stat().st_size, sha256=hashlib.sha256(lib.read_bytes()).hexdigest())))
