"""Prepare reviewed ELF instructions as SHA-guarded, RAM-only compatibility copies."""
from pathlib import Path
import argparse
import base64
import hashlib
import json
import re
import struct

r = Path(__file__).resolve().parent.parent
ap = argparse.ArgumentParser(description=__doc__)
ap.add_argument('spec', type=Path)
args = ap.parse_args()
spec = json.loads(args.spec.read_text(encoding='utf-8'))
label, runtime = spec['label'], spec['runtime']
assert re.fullmatch(r'[a-z0-9-]+', label)
assert re.fullmatch(r'/system/lib64/(?:platformsdk/)?[A-Za-z0-9_.-]+\.so', runtime)
src = (r / spec['source']).resolve(strict=True)
assert src.is_relative_to(r / 'work')
b = src.read_bytes()
sha = lambda x: hashlib.sha256(x).hexdigest()
assert b[:6] == b'\x7fELF\x02\x01' and sha(b) == spec['input_sha256']
phoff = struct.unpack_from('<Q', b, 32)[0]
phsize, phnum = struct.unpack_from('<HH', b, 54)
out, changes = bytearray(b), []
for c in spec['instructions']:
    va = int(c['va'], 0)
    old, new = bytes.fromhex(c['before']), bytes.fromhex(c['after'])
    assert len(old) == len(new) == 4 and va % 4 == 0
    offsets = []
    for i in range(phnum):
        kind, flags, off, addr, _, filesz, _, _ = struct.unpack_from('<IIQQQQQQ', b, phoff+i*phsize)
        if kind == 1 and addr <= va and va+4 <= addr+filesz:
            assert flags & 1
            offsets.append(off+va-addr)
    assert len(offsets) == 1
    offset = offsets[0]
    assert b[offset:offset+4] == old and out[offset:offset+4] == old
    out[offset:offset+4] = new
    changes.append(dict(va=hex(va), offset=offset, before=old.hex(), after=new.hex()))
dest = r / 'work' / (label+'.so')
if dest.exists():
    assert dest.read_bytes() == out
else:
    dest.write_bytes(out)
report = dict(spec, changes=changes, output_sha256=sha(out), vendor_modified=False, original_system_modified=False)
(r / f'analysis/{label}-patch.json').write_text(json.dumps(report, indent=2)+'\n')
script = f'''set -e
B=/busybox
R=/hmos-root
src=$R{runtime}
dst=$R/compat/lib64/{Path(runtime).name}
test ! -e "$dst"
echo "{sha(b)}  $src" | $B sha256sum -c -
$B cp "$src" "$dst"
'''
for c in changes:
    script += f"echo '{base64.b64encode(bytes.fromhex(c['after'])).decode()}' | $B base64 -d | $B dd of=\"$dst\" bs=1 seek={c['offset']} conv=notrunc\n"
script += f'''echo "{sha(out)}  $dst" | $B sha256sum -c -
$B chmod 644 "$dst"
$B mount --bind "$dst" "$src"
$B sha256sum "$src"
echo {label.upper().replace('-', '_')}_RAM_BIND_OK
'''
(r / f'output/apply-{label}-ram.sh').write_text(script, newline='\n')
print(json.dumps(report, indent=2))
