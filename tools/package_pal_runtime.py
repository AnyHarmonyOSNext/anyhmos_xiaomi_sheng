"""Package original stock303 PAL libraries for RAM-only load diagnostics."""
from pathlib import Path
import hashlib
import json
import shutil
import subprocess
import tarfile

r = Path(__file__).resolve().parent.parent
root = r/'work/audio-pal-v1'
(root/'lib64').mkdir(parents=True, exist_ok=True)
vndk = r/'work/stock-audio-runtime/vndk33'
payload = vndk/'apex_payload.img'
listing = subprocess.check_output(['debugfs', '-R', 'ls -p /lib64', str(payload)], text=True,
                                  stderr=subprocess.DEVNULL)
available = {s.split('/')[5] for s in listing.splitlines() if len(s.split('/')) > 6}
report = json.loads((r/'analysis/stock-pal-runtime-inputs.json').read_text())
assert not report['missing'], report['missing']
manifest = {}
for rec in report['files']:
    src = r/rec['local'].replace('\\', '/')
    if src.name == 'PalTest':
        continue
    if rec['partition'] == 'system' and src.name in available:
        src = vndk/src.name
        subprocess.run(['debugfs', '-R', f'dump -p /lib64/{src.name} {src}', str(payload)],
                       capture_output=True, check=True)
    dst = root/'lib64'/src.name
    shutil.copyfile(src, dst)
    manifest[str(dst.relative_to(root))] = dict(source=str(src.relative_to(r)),
        bytes=src.stat().st_size, sha256=hashlib.sha256(src.read_bytes()).hexdigest())
(root/'manifest.json').write_text(json.dumps(manifest, indent=2)+'\n')
archive = r/'output/audio-pal-v1.tar.gz'
with tarfile.open(archive, 'w:gz') as tar:
    for p in sorted(root.rglob('*')):
        if p.is_file():
            info = tar.gettarinfo(str(p), str(p.relative_to(root)))
            info.mode = 0o644
            info.uid = info.gid = 0
            info.uname = info.gname = ''
            with p.open('rb') as f:
                tar.addfile(info, f)
b = archive.read_bytes()
parts = []
for offset in range(0, len(b), 900000):
    p = archive.with_name(archive.name+f'.part{offset//900000:02}')
    p.write_bytes(b[offset:offset+900000])
    parts.append(dict(path=str(p.relative_to(r)), bytes=p.stat().st_size,
                      sha256=hashlib.sha256(p.read_bytes()).hexdigest()))
result = dict(archive=str(archive.relative_to(r)), bytes=len(b),
              sha256=hashlib.sha256(b).hexdigest(), parts=parts)
(r/'analysis/audio-pal-v1-package.json').write_text(json.dumps(result, indent=2)+'\n')
print(json.dumps(result, indent=2))
