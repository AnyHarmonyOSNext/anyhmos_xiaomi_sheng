from pathlib import Path
import subprocess, hashlib, json
r=Path(__file__).resolve().parents[1]
sdk=Path('/root/hmos-work/sdk-6.0.0.47/installed/native')
d=r/'compat/sheng-touch'; src=d/'upstream'; dest=d/'service-v1'; dest.mkdir(exist_ok=True); out=dest/'sheng_thp_bridge'
command=[str(sdk/'llvm/bin/clang++'),'--target=aarch64-linux-ohos','-std=c++20','-O2','-Wall','-Wextra','-Werror','-fno-rtti','-nostdlib++','-include','/root/hmos-work/graphics-deps/sheng-graphics-port/tests/platform_cpp_config.h','-I'+str(src),str(r/'tools/sheng_thp_bridge.cpp'),str(src/'nvt_touch_core.cpp'),str(src/'nvt_finger_filter.cpp'),str(r/'work/donor-hdi-link/libc++.so'),'-o',str(out)]
subprocess.run(command,check=True)
subprocess.run([str(sdk/'llvm/bin/llvm-strip'),str(out)],check=True)
print(json.dumps(dict(bytes=out.stat().st_size,sha256=hashlib.sha256(out.read_bytes()).hexdigest())))
