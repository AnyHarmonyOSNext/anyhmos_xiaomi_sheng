from pathlib import Path
import subprocess, hashlib, json
r=Path(__file__).resolve().parent.parent
b=Path('/root/hmos-work/graphics-deps')
sdk=Path('/root/hmos-work/sdk-6.0.0.47/installed/native')
s=(r/'tools/native_zink_contract_v125.cpp').read_text()
s=s.replace('"egl_window_fixture.h"','"egl_real_window_fixture_v126.h"')
s=s.replace('/data/local/tmp/sheng-zink/libEGL_impl.so','/compat/lib64/libEGL_impl.so')
out=r/'compat/sheng-graphics/zink-cleanup-v126'
src=out/'native_real_egl_window.cpp'; src.write_text(s)
exe=out/'native_real_egl_window'
subprocess.run([str(sdk/'llvm/bin/clang++'),'--target=aarch64-linux-ohos','-std=c++17','-O2','-Wall','-Wextra','-Werror','-fno-exceptions','-fno-rtti','-nostdlib++','-include',str(b/'sheng-graphics-port/tests/platform_cpp_config.h'),'-I'+str(r/'tools'),str(src),str(b/'rom-link/libc++.so'),'-o',str(exe)],check=True)
subprocess.run([str(sdk/'llvm/bin/llvm-strip'),str(exe)],check=True)
print(json.dumps(dict(path=str(exe),bytes=exe.stat().st_size,sha256=hashlib.sha256(exe.read_bytes()).hexdigest())))
