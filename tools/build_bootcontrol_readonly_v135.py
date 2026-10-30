"""WSL: build a read-only, bounded original-HAL probe with original303 Bionic."""
from pathlib import Path
import subprocess
import tarfile
import hashlib
import json
r=Path(__file__).resolve().parent.parent
sdk=Path('/root/hmos-work/sdk-6.0.0.47/installed/native')
d=r/'compat/sheng-bootcontrol/v135'
target=d/'libsheng_bootcontrol_readonly_v135.so'
command=[str(sdk/'llvm/bin/clang'),'--target=aarch64-linux-android33',
    '--sysroot='+str(sdk/'sysroot'),'-isystem',str(sdk/'sysroot/usr/include/aarch64-linux-ohos'),
    '-fuse-ld=lld','-fPIC','-shared','-nostdlib','-mno-outline-atomics',
    '-Wall','-Wextra','-Werror','-O2','-Wl,-z,defs',
    '-L'+str(r/'work/audio-bionic-v1/lib64'),str(r/'tools/bootcontrol_readonly_v135.c'),
    '-lc','-ldl','-o',str(target)]
subprocess.run(command,check=True)
subprocess.run([str(sdk/'llvm/bin/llvm-strip'),str(target)],check=True)
guarded=d/'libsheng_bootcontrol_guarded_v135.so'
markcommand=command.copy();markcommand.insert(1,'-DSHENG_ALLOW_MARK_BOOT_SUCCESS=1');markcommand[-1]=str(guarded)
subprocess.run(markcommand,check=True)
subprocess.run([str(sdk/'llvm/bin/llvm-strip'),str(guarded)],check=True)
archive=r/'output/bootcontrol-readonly-v135.tar.gz'
with tarfile.open(archive,'w:gz') as tar:
    for p in sorted(d.iterdir()):
        if p.is_file():tar.add(p,arcname=p.name)
report=dict(status='built_not_tested_readonly',source='backed-up TWRP recovery_a.img',
    source_sha256='e49349c89ace199c2543cba20edfa5cdcd823fa2bcf42e293eb50bbcaa8c6206',
    files=[dict(name=p.name,bytes=p.stat().st_size,sha256=hashlib.sha256(p.read_bytes()).hexdigest()) for p in d.iterdir()],
    archive=dict(file=str(archive.relative_to(r)),bytes=archive.stat().st_size,sha256=hashlib.sha256(archive.read_bytes()).hexdigest()))
(r/'analysis/bootcontrol-readonly-v135-build.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
print(json.dumps(report,indent=2))
