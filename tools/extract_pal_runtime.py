"""Extract exact stock303 PAL dependencies for isolated compatibility inspection.

Reads official images only. Existing compatible Bionic runtime libraries are
reused. No image, vendor filesystem or device is modified by this tool.
"""
from pathlib import Path
import hashlib
import json
import re
import struct
import subprocess

r = Path(__file__).resolve().parent.parent
base = Path('C:/MIO-KITCHEN-PYSIDE6-5.0.0-PREVIEW/303')
out = r / 'work/stock-pal-runtime'
out.mkdir(exist_ok=True)
exe = 'C:/MIO-KITCHEN-PYSIDE6-5.0.0-PREVIEW/bin/Windows/AMD64/extract.erofs.exe'
runtime = r / 'work/audio-bionic-v1'

def needed(p):
    b = p.read_bytes()
    if not b.startswith(b'\x7fELF\x02\x01'):
        return []
    off = struct.unpack_from('<Q', b, 40)[0]
    size, count = struct.unpack_from('<HH', b, 58)
    sections = [struct.unpack_from('<IIQQQQIIQQ', b, off + i * size) for i in range(count)]
    dyn = next((s for s in sections if s[1] == 6), None)
    if dyn is None:
        return []
    st = sections[dyn[6]]
    strings = b[st[4]:st[4]+st[5]]
    return [strings[v:].split(b'\0', 1)[0].decode() for pos in range(dyn[4], dyn[4]+dyn[5], 16)
            for tag, v in [struct.unpack_from('<qQ', b, pos)] if tag == 1]

available = {}
for part, listing in [('system', 'stock-audio-system-list-system-lib64.txt'),
                      ('system_ext', 'stock-audio-list-system_ext-lib64.txt'),
                      ('vendor', 'stock-audio-list-vendor-lib64.txt'),
                      ('odm', 'stock-audio-list-odm-lib64.txt')]:
    for path in re.findall(r'type=FILE .*?fsConfig=\[([^ ]+)', (r/'analysis'/listing).read_text()):
        if '/hwasan/' not in path:
            available[Path(path).name] = (part, path)
available['PalTest'] = ('vendor', '/bin/PalTest')
queue = ['libar-pal.so', 'PalTest']
seen, files, missing = set(), [], []
while queue:
    name = queue.pop(0)
    if name in seen:
        continue
    seen.add(name)
    if (runtime/'lib64'/name).is_file():
        continue
    if name not in available:
        missing.append(name)
        continue
    part, path = available[name]
    dest = out / part / path.lstrip('/')
    if not dest.is_file():
        subprocess.run([exe, '-i', str(base/(part+'.img')), '-X', path, '-o', str(out), '-s'],
                       capture_output=True, check=True)
    assert dest.is_file(), dest
    deps = needed(dest)
    files.append(dict(partition=part, path=path, local=str(dest.relative_to(r)),
                      bytes=dest.stat().st_size, sha256=hashlib.sha256(dest.read_bytes()).hexdigest(), needed=deps))
    queue.extend(deps)
report = dict(files=files, missing=missing)
(r/'analysis/stock-pal-runtime-inputs.json').write_text(json.dumps(report, indent=2)+'\n', encoding='utf-8')
for f in files:
    print(f['path'], f['bytes'], ','.join(f['needed']))
print('MISSING', missing)
