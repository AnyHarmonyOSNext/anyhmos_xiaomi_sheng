"""WSL: package exact original Bionic/AGM inputs into an isolated RAM runtime.

No mixer changes or audio playback. Payload parts obey the 1 MiB USB limit.
"""
from pathlib import Path
import hashlib
import json
import re
import shutil
import struct
import subprocess
import tarfile

r = Path(__file__).resolve().parent.parent
source = r / 'work/stock-audio-runtime'
vndk = source / 'vndk33'
payload = vndk / 'apex_payload.img'
root = r / 'work/audio-bionic-v1'
for name in ['lib64', 'bin', 'licenses']:
    (root / name).mkdir(parents=True, exist_ok=True)
report = json.loads((r / 'analysis/stock-audio-runtime-inputs.json').read_text())

def needed(p):
    lines = subprocess.check_output(['/root/hmos-work/sdk-6.0.0.47/installed/native/llvm/bin/llvm-readelf', '-d', str(p)], text=True)
    return re.findall(r'\(NEEDED\).*?\[(.*?)\]', lines)

listing = subprocess.check_output(['debugfs', '-R', 'ls -p /lib64', str(payload)], text=True, stderr=subprocess.DEVNULL)
available = {line.split('/')[5] for line in listing.splitlines() if len(line.split('/')) > 6}
provenance = {}
for rec in report['files']:
    p = r / rec['local'].replace('\\', '/')
    name = p.name
    if p.suffix != '.so' and name not in ['libc++.so', 'agmplay', 'linker64']:
        continue
    if p.suffix == '.so' or name == 'libc++.so':
        dest = root / 'lib64' / name
        if name in available and rec['partition'] == 'system':
            temp = vndk / name
            subprocess.run(['debugfs', '-R', f'dump -p /lib64/{name} {temp}', str(payload)], check=True, capture_output=True)
            assert temp.is_file()
            p = temp
    else:
        dest = root / 'bin' / name
    shutil.copy2(p, dest)
    provenance[str(dest.relative_to(root))] = str(p.relative_to(r))
for name in ['libaudioroute.so']:
    assert name in available
    temp = vndk / name
    subprocess.run(['debugfs', '-R', f'dump -p /lib64/{name} {temp}', str(payload)], check=True, capture_output=True)
    shutil.copy2(temp, root / 'lib64' / name)
    provenance['lib64/' + name] = str(temp.relative_to(r))

unresolved = set()
for p in (root / 'lib64').iterdir():
    unresolved.update(name for name in needed(p) if not (root / 'lib64' / name).is_file())
assert not unresolved, unresolved
manifest = dict(scope='Exact original303 ELF files, flattened local library search path, no binary patches',
                files={str(p.relative_to(root)): dict(source=provenance[str(p.relative_to(root))],
                  bytes=p.stat().st_size, sha256=hashlib.sha256(p.read_bytes()).hexdigest())
                  for p in root.rglob('*') if p.is_file() and str(p.relative_to(root)) in provenance})
(root / 'manifest.json').write_text(json.dumps(manifest, indent=2) + '\n')
archive = r / 'output/audio-bionic-v1.tar.gz'
with tarfile.open(archive, 'w:gz') as tar:
    for p in sorted(root.rglob('*')):
        if p.is_file():
            info = tar.gettarinfo(str(p), str(p.relative_to(root)))
            info.mode = 0o755 if info.name.startswith('bin/') else 0o644
            info.uid = info.gid = 0
            info.uname = info.gname = ''
            with p.open('rb') as f:
                tar.addfile(info, f)
b = archive.read_bytes()
parts = []
for i in range(0, len(b), 900000):
    p = archive.with_name(archive.name + f'.part{i//900000:02}')
    p.write_bytes(b[i:i+900000])
    parts.append(dict(path=str(p.relative_to(r)), bytes=p.stat().st_size, sha256=hashlib.sha256(p.read_bytes()).hexdigest()))
result = dict(archive=str(archive.relative_to(r)), bytes=len(b), sha256=hashlib.sha256(b).hexdigest(), parts=parts)
(r / 'analysis/audio-bionic-v1-package.json').write_text(json.dumps(result, indent=2)+'\n')
print(json.dumps(result, indent=2))
