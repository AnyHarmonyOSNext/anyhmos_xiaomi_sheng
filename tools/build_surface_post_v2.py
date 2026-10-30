from pathlib import Path
import subprocess,hashlib,json
r=Path('/mnt/c/SHENG_WORKSPACE')
sdk=Path('/root/hmos-work/sdk-6.0.0.47/installed/native')
out=r/'compat/sheng-graphics/surface-post-v2'
out.mkdir(exist_ok=True)
p=out/'libsheng_surface_diagnostic.so'
subprocess.run([str(sdk/'llvm/bin/clang++'),'--target=aarch64-linux-ohos','-std=c++17','-O2','-Wall','-Wextra','-Werror','-fno-exceptions','-fno-rtti','-nostdlib++','-shared','-fPIC','-include','/root/hmos-work/graphics-deps/sheng-graphics-port/tests/platform_cpp_config.h',str(r/'tools/native_surface_post_v2.cpp'),str(r/'tools/native_buffer_import_observer.S'),str(r/'work/donor-hdi-link/libc++.so'),'-o',str(p)],check=True)
subprocess.run([str(sdk/'llvm/bin/llvm-strip'),str(p)],check=True)
report=dict(bytes=p.stat().st_size,sha256=hashlib.sha256(p.read_bytes()).hexdigest(),mode='same-thread inline only when gate file exists; cross-thread original queue retained')
(out/'manifest.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps(report))
