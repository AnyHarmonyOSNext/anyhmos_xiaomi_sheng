"""WSL: use actual Android clang14 libc++ headers, original303 shared imports."""
from pathlib import Path
import subprocess
import tarfile
import hashlib
import json
r=Path(__file__).resolve().parent.parent
sdk=Path('/root/hmos-work/sdk-6.0.0.47/installed/native')
headers=Path('/root/hmos-work/clang-prebuilt/clang-r450784e/include/c++/v1')
assert (headers/'functional').is_file()
d=r/'compat/sheng-bluetooth/backend-v136'
out=d/'libsheng_bt_readonly_v136.so'
command=[str(sdk/'llvm/bin/clang++'),'--target=aarch64-linux-android33',
    '--sysroot='+str(sdk/'sysroot'),'-isystem',str(sdk/'sysroot/usr/include/aarch64-linux-ohos'),
    '-nostdinc++','-isystem',str(headers),'-std=c++17','-fuse-ld=lld',
    '-fPIC','-shared','-nostdlib','-mno-outline-atomics','-fno-exceptions',
    '-Wall','-Wextra','-Werror','-O2','-Wl,-z,defs',
    '-L'+str(r/'work/audio-bionic-v1/lib64'),str(r/'tools/bluetooth_backend_readonly_v136.cpp'),
    '-lc++','-lc','-ldl','-o',str(out)]
subprocess.run(command,check=True)
subprocess.run([str(sdk/'llvm/bin/llvm-strip'),str(out)],check=True)
files={str(p.relative_to(d)):dict(bytes=p.stat().st_size,sha256=hashlib.sha256(p.read_bytes()).hexdigest())
       for p in d.rglob('*') if p.is_file() and p.name!='SHA256SUMS'}
(d/'SHA256SUMS').write_text(''.join(v['sha256']+'  '+n+'\n' for n,v in sorted(files.items())),encoding='utf-8')
archive=r/'output/bluetooth-backend-readonly-v136.tar.gz'
with tarfile.open(archive,'w:gz') as t:
    for p in sorted(d.rglob('*')):
        if p.is_file():t.add(p,arcname=str(p.relative_to(d)))
assert archive.stat().st_size<=1048576
report=dict(status='built_not_loaded_no_hardware_init',android_libcpp_abi_version=1,
    android_libcpp_header_source=str(headers),files=files,
    archive=dict(file=str(archive.relative_to(r)),bytes=archive.stat().st_size,sha256=hashlib.sha256(archive.read_bytes()).hexdigest()))
(r/'analysis/bluetooth-readonly-v136-build.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
print(json.dumps(dict(probe=files[out.name],archive=report['archive']),indent=2))
