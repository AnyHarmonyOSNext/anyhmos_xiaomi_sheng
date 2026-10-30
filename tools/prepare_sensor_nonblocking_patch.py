"""Replace the donor's 10s sensor-service load with its original nonblocking query."""
from pathlib import Path
import base64
import hashlib
import json
import struct

r = Path(__file__).resolve().parent.parent
b = (r / 'work/hmos_system/system/system/lib64/platformsdk/libsensor_client.z.so').read_bytes()
sha = lambda x: hashlib.sha256(x).hexdigest()
assert sha(b) == 'b99fefc405501762340adbbc6aaabf314e421ebcaa54f73879b368c415912bef'
va = 0x22570
phoff = struct.unpack_from('<Q', b, 32)[0]
phsize, phnum = struct.unpack_from('<HH', b, 54)
offsets = []
for i in range(phnum):
    kind, flags, off, addr, _, filesz, _, _ = struct.unpack_from('<IIQQQQQQ', b, phoff+i*phsize)
    if kind == 1 and addr <= va and va+4 <= addr+filesz:
        assert flags & 1
        offsets.append(off+va-addr)
assert len(offsets) == 1
offset = offsets[0]
old, new = bytes.fromhex('a93e40f9'), bytes.fromhex('a91640f9')
assert b[offset:offset+4] == old
out = bytearray(b)
out[offset:offset+4] = new
dest = r / 'work/libsensor_client.nonblocking.z.so'
if dest.exists():
    assert dest.read_bytes() == out
else:
    dest.write_bytes(out)
report = dict(name='donor sensor SDK nonblocking SA3601 query', va=hex(va),
              input_sha256=sha(b), output_sha256=sha(out),
              changes=[dict(offset=offset, before=old.hex(), after=new.hex())],
              semantics='Use CheckSystemAbility(int) vtable+40 instead of LoadSystemAbility(int,10000) vtable+120; keep original null/error path',
              vendor_modified=False, original_system_modified=False)
(r / 'analysis/sensor-nonblocking-patch.json').write_text(json.dumps(report, indent=2)+'\n')
script = f'''set -e
B=/busybox
R=/hmos-root
src=$R/system/lib64/platformsdk/libsensor_client.z.so
dst=$R/compat/lib64/libsensor_client.z.so
test ! -e "$dst"
echo "{sha(b)}  $src" | $B sha256sum -c -
$B cp "$src" "$dst"
echo '{base64.b64encode(new).decode()}' | $B base64 -d | $B dd of="$dst" bs=1 seek={offset} conv=notrunc
echo "{sha(out)}  $dst" | $B sha256sum -c -
$B chmod 644 "$dst"
$B mount --bind "$dst" "$src"
$B sha256sum "$src"
echo SENSOR_NONBLOCKING_RAM_BIND_OK
'''
(r / 'output/apply-sensor-nonblocking-ram.sh').write_text(script, newline='\n')
print(json.dumps(report, indent=2))
