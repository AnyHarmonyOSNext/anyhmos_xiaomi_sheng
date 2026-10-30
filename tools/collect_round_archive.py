"""Export an explicitly named compatibility runtime directory in Recovery."""
from pathlib import Path
import subprocess,sys,tarfile,hashlib,json,re,datetime
r=Path(__file__).resolve().parent.parent
directory,boot_id=sys.argv[1:]
assert re.fullmatch(r'v\d+-runtime-[a-zA-Z0-9-]+',directory)
assert re.fullmatch(r'[a-f0-9-]{36}',boot_id)
adb=str(r/'output/platform-tools/adb.exe')
state=subprocess.check_output([adb,'devices'],text=True)
assert re.search(r'^YOUR_DEVICE_SERIAL\s+recovery$',state,re.M),state
archive=r/'output/logs'/f'{directory}-{datetime.datetime.now():%Y%m%d-%H%M%S}.tar'
assert not archive.exists()
with archive.open('xb') as dst:
 subprocess.run([adb,'-s','YOUR_DEVICE_SERIAL','exec-out','tar','-C','/data/hmos-compat','-cf','-',directory,'probe-'+boot_id+'.log'],stdout=dst,check=True)
with tarfile.open(archive) as tar:
 entries=tar.getmembers()
 assert entries and all(not x.name.startswith('/') and '..' not in Path(x.name).parts for x in entries)
 assert any(x.name.endswith('/boot-id.txt') for x in entries)
report=dict(file=str(archive.relative_to(r)),bytes=archive.stat().st_size,
 sha256=hashlib.sha256(archive.read_bytes()).hexdigest(),entries=len(entries))
(r/'analysis'/(directory+'-archive.json')).write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps(report))
