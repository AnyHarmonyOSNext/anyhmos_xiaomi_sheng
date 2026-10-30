from pathlib import Path
import subprocess
adb=str(Path('output/platform-tools/adb.exe').resolve());d=Path('analysis/device-probe-v1');d.mkdir(exist_ok=True)
r=subprocess.run([adb,'-s','YOUR_DEVICE_SERIAL','shell','ls /metadata/hmos-debug/probe-*.log'],capture_output=True,check=True)
for p in r.stdout.decode().splitlines():
 p=p.strip()
 if not p.startswith('/metadata/hmos-debug/probe-') or not p.endswith('.log'):continue
 r=subprocess.run([adb,'-s','YOUR_DEVICE_SERIAL','exec-out','cat',p],capture_output=True,check=True);f=d/Path(p).name;f.write_bytes(r.stdout);print(f,len(r.stdout));print(r.stdout.decode(errors='replace')[-12000:])
