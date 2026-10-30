"""Read-only official303 dependency closure for an isolated Qualcomm HCI backend."""
from pathlib import Path
import json
import subprocess
import hashlib
import re
import shutil

r=Path(__file__).resolve().parent.parent
source=r/'work/stock-bluetooth-v136'
root=r/'compat/sheng-bluetooth/backend-v136/lib64';root.mkdir(parents=True,exist_ok=True)
audio=r/'work/audio-bionic-v1/lib64'
vndk=r/'work/stock-audio-runtime/vndk33'
payload=vndk/'apex_payload.img'
extract='C:/MIO-KITCHEN-PYSIDE6-5.0.0-PREVIEW/bin/Windows/AMD64/extract.erofs.exe'
vendor='C:/MIO-KITCHEN-PYSIDE6-5.0.0-PREVIEW/303/vendor.img'
def wsl(p):return '/mnt/c/'+str(p).replace('\\','/').split(':/',1)[1]
reader='/root/hmos-work/sdk-6.0.0.47/installed/native/llvm/bin/llvm-readelf'
def needed(p):
    s=subprocess.check_output(['wsl.exe','--',reader,'-d',wsl(p)],text=True)
    return re.findall(r'\(NEEDED\).*?\[(.*?)\]',s)
listing=subprocess.check_output(['wsl.exe','--','debugfs','-R','ls -p /lib64',wsl(payload)],text=True,stderr=subprocess.DEVNULL)
available={line.split('/')[5] for line in listing.splitlines() if len(line.split('/'))>6}
queue=['android.hardware.bluetooth@1.0-impl-qti.so']
records={}
while queue:
    name=queue.pop(0)
    if name in records:continue
    assert re.fullmatch(r'[a-zA-Z0-9_.@+-]+',name)
    reused=(audio/name).is_file()
    if reused:p=audio/name
    else:
        p=source/'vendor/lib64'/name
        hw=source/'vendor/lib64/hw'/name
        if hw.is_file():p=hw
        if not p.is_file() and name in available:
            p=vndk/name
            if not p.is_file():
                subprocess.run(['wsl.exe','--','debugfs','-R',f'dump -p /lib64/{name} {wsl(p)}',wsl(payload)],check=True,capture_output=True)
        if not p.is_file():
            subprocess.run([extract,'-i',vendor,'-X','/lib64/'+name,'-o',str(source),'-s'],check=True,capture_output=True)
            p=source/'vendor/lib64'/name
        assert p.is_file(),name
        shutil.copy2(p,root/name)
    dependencies=needed(p)
    records[name]=dict(source=str(p.relative_to(r)),reused_audio_runtime=reused,
        bytes=p.stat().st_size,sha256=hashlib.sha256(p.read_bytes()).hexdigest(),needed=dependencies)
    queue.extend(dependencies)
assert all(n in records for d in records.values() for n in d['needed'])
report=dict(status='offline_dependency_closure_only',files=records,
    new_library_bytes=sum(v['bytes'] for v in records.values() if not v['reused_audio_runtime']),
    original_vendor_unchanged=True,no_hardware_initialization=True)
(r/'analysis/bluetooth-runtime-v136.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
print(json.dumps(dict(new_libraries=[k for k,v in records.items() if not v['reused_audio_runtime']],
    reused_libraries=[k for k,v in records.items() if v['reused_audio_runtime']],new_bytes=report['new_library_bytes']),indent=2))
