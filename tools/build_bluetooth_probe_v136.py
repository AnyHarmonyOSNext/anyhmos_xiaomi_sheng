"""WSL: isolated Bionic probe, actual Android libc++ headers/imports."""
from pathlib import Path
import subprocess,sys,hashlib,json
r=Path(__file__).resolve().parent.parent
name=sys.argv[1]
assert name in ('identity','initialize','bridge')
sdk=Path('/root/hmos-work/sdk-6.0.0.47/installed/native')
headers=Path('/root/hmos-work/clang-prebuilt/clang-r450784e/include/c++/v1')
out=r/f'output/libsheng_bt_{name}_v136.so'
command=[str(sdk/'llvm/bin/clang++'),'--target=aarch64-linux-android33',
    '--sysroot='+str(sdk/'sysroot'),'-isystem',str(sdk/'sysroot/usr/include/aarch64-linux-ohos'),
    '-nostdinc++','-isystem',str(headers),'-std=c++17','-fuse-ld=lld',
    '-fPIC','-shared','-nostdlib','-mno-outline-atomics','-fno-exceptions',
    '-Wall','-Wextra','-Werror','-O2','-Wl,-z,defs',
    '-L'+str(r/'work/audio-bionic-v1/lib64'),str(r/f'tools/bluetooth_{name}_v136.cpp'),
    '-lc++','-lc','-ldl','-o',str(out)]
subprocess.run(command,check=True)
subprocess.run([str(sdk/'llvm/bin/llvm-strip'),str(out)],check=True)
report=dict(file=str(out.relative_to(r)),bytes=out.stat().st_size,sha256=hashlib.sha256(out.read_bytes()).hexdigest())
(r/f'analysis/bluetooth-{name}-v136-build.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
print(json.dumps(report))
