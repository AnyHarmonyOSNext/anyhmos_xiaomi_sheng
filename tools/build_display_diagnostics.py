"""Build small diagnostics using the existing pinned OHOS SDK and donor C++ ABI."""
from pathlib import Path
import subprocess, json, hashlib
r=Path('/mnt/c/SHENG_WORKSPACE')
sdk=Path(json.loads(Path('/root/hmos-work/sdk-6.0.0.47/installation.json').read_text())['sdk'])
out=r/'compat/debug-tools'
cpp=r/'work/hmos_system/system/system/lib64/chipset-sdk-sp/libc++.so'
for name,language in [('native_display_wake','c++'),('capture_scanout','c')]:
    args=[str(sdk/'llvm/bin'/('clang++' if language=='c++' else 'clang')),
          '--target=aarch64-linux-ohos','-Os','-Wall','-Wextra','-Werror']
    if language=='c++':
        args+=['-std=c++17','-fno-exceptions','-fno-rtti','-nostdlib++','-include',
               '/root/hmos-work/graphics-deps/sheng-graphics-port/tests/platform_cpp_config.h']
    args += [str(r/'tools'/(name+('.cpp' if language=='c++' else '.c')))]
    if language=='c++': args += [str(cpp)]
    args+=['-o',str(out/name)]
    subprocess.run(args,check=True)
    subprocess.run([str(sdk/'llvm/bin/llvm-strip'),str(out/name)],check=True)
    data=(out/name).read_bytes()
    print(json.dumps(dict(name=name,bytes=len(data),sha256=hashlib.sha256(data).hexdigest())))
