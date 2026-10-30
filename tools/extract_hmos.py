from pathlib import Path
import subprocess
exe='C:/MIO-KITCHEN-PYSIDE6-5.0.0-PREVIEW/bin/Windows/AMD64/extract.erofs.exe'; image='C:/MIO-KITCHEN-PYSIDE6-5.0.0-PREVIEW/hmos/system.img'; out=Path('work/hmos_system').resolve(); out.mkdir(exist_ok=True)
paths=['/system/etc','/system/bin/init','/system/bin/ueventd','/system/bin/hdcd','/system/bin/sh','/system/bin/toybox','/system/bin/param','/system/lib64/ld-musl-aarch64.so.1','/init']
for p in paths:
 r=subprocess.run([exe,'-i',image,'-X',p,'-o',str(out),'-s'],capture_output=True); print(p,r.returncode,r.stdout.decode(errors='replace')[-500:],r.stderr.decode(errors='replace')[-500:])
