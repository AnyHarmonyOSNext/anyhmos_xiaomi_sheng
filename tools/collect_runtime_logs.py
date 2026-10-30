from pathlib import Path
import subprocess,hashlib,re,json
r=Path(__file__).resolve().parent.parent
adb=str(r/'output/platform-tools/adb.exe')
paths=subprocess.check_output([adb,'-s','YOUR_DEVICE_SERIAL','shell','ls /data/hmos-compat/probe-*.log'],text=True).splitlines()
report=[]
for path in paths:
 path=path.strip()
 assert re.fullmatch(r'/data/hmos-compat/probe-[a-f0-9-]+\.log',path)
 data=subprocess.check_output([adb,'-s','YOUR_DEVICE_SERIAL','exec-out','cat',path])
 dst=r/'output/logs'/('persistent-'+Path(path).name)
 if dst.exists():assert dst.read_bytes()==data
 else:dst.write_bytes(data)
 report.append({'file':str(dst.relative_to(r)),'bytes':len(data),'sha256':hashlib.sha256(data).hexdigest()})
print(json.dumps(report,indent=2))
