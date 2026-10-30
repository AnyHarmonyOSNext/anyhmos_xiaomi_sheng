"""Extract only untouched official audio routing/amp firmware references."""
from pathlib import Path
import hashlib
import json
import re
import subprocess
r=Path(__file__).resolve().parent.parent
exe='C:/MIO-KITCHEN-PYSIDE6-5.0.0-PREVIEW/bin/Windows/AMD64/extract.erofs.exe'
base=Path('C:/MIO-KITCHEN-PYSIDE6-5.0.0-PREVIEW/303')
out=r/'work/stock-audio-reference';out.mkdir(exist_ok=True)
report=[]
for part in ['vendor','odm']:
    image=base/f'{part}.img'
    listing=subprocess.check_output([exe,'-i',str(image),'-P','/etc','-s']).decode('utf-8',errors='replace')
    paths=[]
    for line in listing.splitlines():
        m=re.search(r'type=FILE .*fsConfig=\[(/[^ ]+)',line)
        if not m:continue
        p=m[1]
        if any(word in Path(p).name.lower() for word in ['mixer_paths','audio_platform_info','cs35l43','cs35l41']):paths.append(p)
    for p in paths:
        subprocess.run([exe,'-i',str(image),'-X',p,'-o',str(out),'-s'],check=True,capture_output=True)
        f=out/part/p.lstrip('/')
        if not f.exists():
            matches=list(out.rglob(Path(p).name));assert len(matches)==1,(p,matches)
            f=matches[0]
        report.append(dict(partition=part,path=p,local=str(f.relative_to(r)),bytes=f.stat().st_size,sha256=hashlib.sha256(f.read_bytes()).hexdigest()))
(r/'analysis/stock-audio-references.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
print(json.dumps(report,indent=2))
