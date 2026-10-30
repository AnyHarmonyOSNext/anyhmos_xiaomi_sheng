"""Extract the stock v33 compatibility APEX payload without mounting it."""
from pathlib import Path
import subprocess
import zipfile
import json
import hashlib

r = Path(__file__).resolve().parent.parent
out = r / 'work/stock-audio-runtime'
exe = 'C:/MIO-KITCHEN-PYSIDE6-5.0.0-PREVIEW/bin/Windows/AMD64/extract.erofs.exe'
image = 'C:/MIO-KITCHEN-PYSIDE6-5.0.0-PREVIEW/303/system_ext.img'
subprocess.run([exe, '-i', image, '-X', '/apex/com.android.vndk.v33.apex', '-o', str(out), '-s'], capture_output=True, check=True)
apex = out / 'system_ext/apex/com.android.vndk.v33.apex'
assert apex.is_file()
d = out / 'vndk33'
d.mkdir(exist_ok=True)
with zipfile.ZipFile(apex) as archive:
    with archive.open('apex_payload.img') as source, (d / 'apex_payload.img').open('wb') as dest:
        import shutil
        shutil.copyfileobj(source, dest)
meta = {str(p.relative_to(r)): dict(bytes=p.stat().st_size, sha256=hashlib.sha256(p.read_bytes()).hexdigest())
        for p in [apex, d / 'apex_payload.img']}
(r / 'analysis/stock-audio-vndk33-apex.json').write_text(json.dumps(meta, indent=2)+'\n')
print(json.dumps(meta, indent=2))
