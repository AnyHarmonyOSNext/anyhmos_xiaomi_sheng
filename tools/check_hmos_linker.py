from pathlib import Path
import subprocess
adb=str(Path('output/platform-tools/adb.exe').resolve());out=Path('analysis/hmos-linker-check');out.mkdir(exist_ok=True)
for name,args in [('help',['--help']),('dependencies',['--list','/system/bin/init'])]:
 cmd='timeout 15 chroot /system_root /system/lib/ld-musl-aarch64.so.1 '+' '.join(args)
 try:r=subprocess.run([adb,'-s','YOUR_DEVICE_SERIAL','shell',cmd],capture_output=True,timeout=20)
 except subprocess.TimeoutExpired: print(name,'host timeout');continue
 b=r.stdout+r.stderr;(out/(name+'.txt')).write_bytes(b);print(name,'exit',r.returncode,'bytes',len(b));print(b.decode(errors='replace')[:7000])
