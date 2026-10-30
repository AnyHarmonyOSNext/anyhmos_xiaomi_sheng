from pathlib import Path
import subprocess, hashlib, json
r=Path('/mnt/c/SHENG_WORKSPACE')
b=Path('/root/hmos-work/graphics-deps')
sdk=Path('/root/hmos-work/sdk-6.0.0.47/installed/native')
out=r/'compat/sheng-graphics/egl-resize-v144'; out.mkdir(exist_ok=True)
exe=out/'native_egl_resize'
subprocess.run([str(sdk/'llvm/bin/clang++'),'--target=aarch64-linux-ohos','-std=c++17','-O2','-Wall','-Wextra','-Werror','-fno-exceptions','-fno-rtti','-nostdlib++','-include',str(b/'sheng-graphics-port/tests/platform_cpp_config.h'),'-I'+str(r/'tools'),str(r/'tools/native_egl_resize_v144.cpp'),str(b/'rom-link/libc++.so'),'-o',str(exe)],check=True)
subprocess.run([str(sdk/'llvm/bin/llvm-strip'),str(exe)],check=True)
print(json.dumps(dict(bytes=exe.stat().st_size,sha256=hashlib.sha256(exe.read_bytes()).hexdigest())))
