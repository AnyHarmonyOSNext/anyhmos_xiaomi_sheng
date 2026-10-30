"""Extract exact original audio userspace inputs for a separate /compat runtime.

Only reads the official images. Never writes vendor or an image file.
"""
from pathlib import Path
import hashlib
import json
import re
import struct
import subprocess

r = Path(__file__).resolve().parent.parent
base = Path('C:/MIO-KITCHEN-PYSIDE6-5.0.0-PREVIEW/303')
out = r / 'work/stock-audio-runtime'
out.mkdir(exist_ok=True)
exe = 'C:/MIO-KITCHEN-PYSIDE6-5.0.0-PREVIEW/bin/Windows/AMD64/extract.erofs.exe'

def extract(part, path):
    image = base / (part + '.img')
    subprocess.run([exe, '-i', str(image), '-X', path, '-o', str(out), '-s'], capture_output=True, check=True)
    f = out / part / path.lstrip('/')
    assert f.is_file(), f
    return f

def needed(p):
    b = p.read_bytes()
    if not b.startswith(b'\x7fELF\x02\x01'):
        return []
    off = struct.unpack_from('<Q', b, 40)[0]
    size, count, names_index = struct.unpack_from('<HHH', b, 58)
    sections = [struct.unpack_from('<IIQQQQIIQQ', b, off + i * size) for i in range(count)]
    names = sections[names_index]
    strings = b[names[4]:names[4]+names[5]]
    table = {strings[s[0]:].split(b'\0', 1)[0].decode(): s for s in sections}
    if '.dynamic' not in table:
        return []
    dyn = table['.dynamic']
    st = sections[dyn[6]]
    strings = b[st[4]:st[4]+st[5]]
    return [strings[v:].split(b'\0', 1)[0].decode() for pos in range(dyn[4], dyn[4]+dyn[5], 16)
            for tag, v in [struct.unpack_from('<qQ', b, pos)] if tag == 1]

listing = (r / 'analysis/stock-audio-list-vendor-lib64.txt').read_text()
vendor_libs = {Path(p).name: p for p in re.findall(r'type=FILE .*fsConfig=\[(/lib64/[^ ]+)', listing)}
queue = ['libagm.so', 'libar-gsl.so', 'libar-gpr.so', 'libar-acdb.so', 'libagmmixer.so']
seen = set()
files = []
missing = set()
while queue:
    name = queue.pop(0)
    if name in seen:
        continue
    seen.add(name)
    if name not in vendor_libs:
        missing.add(name)
        continue
    f = extract('vendor', vendor_libs[name])
    dependencies = needed(f)
    files.append(dict(partition='vendor', path=vendor_libs[name], local=str(f.relative_to(r)),
                      bytes=f.stat().st_size, sha256=hashlib.sha256(f.read_bytes()).hexdigest(), needed=dependencies))
    queue.extend(dependencies)
for part, path in [('vendor', '/bin/agmplay'), ('odm', '/etc/acdbdata/Forte/Forte_acdb_cal.acdb'),
                   ('odm', '/etc/acdbdata/Forte/Forte_workspaceFileXml.qwsp'),
                   ('odm', '/etc/audio/sku_kalama/resourcemanager_kalama_mtp.xml'),
                   ('odm', '/etc/init/init.cirrus.rc')]:
    f = extract(part, path)
    files.append(dict(partition=part, path=path, local=str(f.relative_to(r)), bytes=f.stat().st_size,
                      sha256=hashlib.sha256(f.read_bytes()).hexdigest(), needed=needed(f)))
for p in re.findall(r'type=FILE .*fsConfig=\[(/firmware/[^ ]+)', (r / 'analysis/stock-audio-list-odm-firmware.txt').read_text()):
    if 'cs35l43' in p:
        f = extract('odm', p)
        files.append(dict(partition='odm', path=p, local=str(f.relative_to(r)), bytes=f.stat().st_size,
                          sha256=hashlib.sha256(f.read_bytes()).hexdigest(), needed=[]))
for directory in ['/system/bin', '/system/lib64', '/system/apex']:
    result = subprocess.run([exe, '-i', str(base / 'system.img'), '-P', directory, '-s'], capture_output=True)
    (r / 'analysis' / ('stock-audio-system-list' + directory.replace('/', '-') + '.txt')).write_text(result.stdout.decode('utf-8', errors='replace'), encoding='utf-8')
report = dict(files=files, missing_from_vendor=sorted(missing))
system_listing = (r / 'analysis/stock-audio-system-list-system-lib64.txt').read_text()
system_libs = {Path(p).name: p for p in re.findall(r'type=FILE .*fsConfig=\[(/system/lib64/[^ ]+)', system_listing)
               if '/hwasan/' not in p}
result = subprocess.run([exe, '-i', str(base / 'system_ext.img'), '-P', '/lib64', '-s'], capture_output=True, check=True)
ext_listing = result.stdout.decode('utf-8', errors='replace')
(r / 'analysis/stock-audio-list-system_ext-lib64.txt').write_text(ext_listing, encoding='utf-8')
ext_libs = {Path(p).name: p for p in re.findall(r'type=FILE .*fsConfig=\[(/lib64/[^ ]+)', ext_listing)}
queue = sorted(missing)
missing = set()
seen = set()
while queue:
    name = queue.pop(0)
    if name in seen or any(Path(x['path']).name == name for x in files):
        continue
    seen.add(name)
    if name in system_libs:
        part, path = 'system', system_libs[name]
    elif name in ext_libs:
        part, path = 'system_ext', ext_libs[name]
    else:
        missing.add(name)
        continue
    f = extract(part, path)
    dependencies = needed(f)
    files.append(dict(partition=part, path=path, local=str(f.relative_to(r)), bytes=f.stat().st_size,
                      sha256=hashlib.sha256(f.read_bytes()).hexdigest(), needed=dependencies))
    queue.extend(dependencies)
f = extract('system', '/system/bin/bootstrap/linker64')
files.append(dict(partition='system', path='/system/bin/bootstrap/linker64', local=str(f.relative_to(r)),
                  bytes=f.stat().st_size, sha256=hashlib.sha256(f.read_bytes()).hexdigest(), needed=needed(f)))
report['unresolved'] = sorted(missing)
(r / 'analysis/stock-audio-runtime-inputs.json').write_text(json.dumps(report, indent=2)+'\n', encoding='utf-8')
for f in files:
    print(f['partition'], f['path'], f['bytes'], 'NEEDED=' + ','.join(f['needed']))
print('UNRESOLVED=' + ','.join(sorted(missing)))
