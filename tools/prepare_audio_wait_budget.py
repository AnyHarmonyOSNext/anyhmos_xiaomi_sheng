"""Bound only the donor audio volume-group enumeration retry budget.

The donor's SHA and executable PT_LOAD mapping are mandatory guards. The
original lookup, locking, return values, CFI and error paths remain intact.
"""
from pathlib import Path
import hashlib
import json
import struct

r = Path(__file__).resolve().parent.parent
p = r / 'work/hmos_system/system/system/lib64/libaudio_policy_service.z.so'
b = p.read_bytes()
sha = lambda data: hashlib.sha256(data).hexdigest()
assert sha(b) == 'a861efe809d18e8f2a5586d7834e649982477f57a4731696f7185fe63f725844'
assert b[:6] == b'\x7fELF\x02\x01'
assert struct.unpack_from('<H', b, 18)[0] == 183
phoff = struct.unpack_from('<Q', b, 32)[0]
phsize, phnum = struct.unpack_from('<HH', b, 54)

def offset(va):
    for i in range(phnum):
        typ, flags, off, addr, _, size, _, _ = struct.unpack_from('<II6Q', b, phoff + i * phsize)
        if typ == 1 and addr <= va < addr + size:
            assert flags & 1
            return off + va - addr
    raise ValueError(hex(va))

va = 0x318178
pos = offset(va)
assert b[pos:pos + 4].hex() == '36038052'  # mov w22, #25
after = bytes.fromhex('56008052')          # mov w22, #2
assert (int.from_bytes(after, 'little') >> 5) & 0xffff == 2
out = bytearray(b)
out[pos:pos + 4] = after
assert [i for i, (a, z) in enumerate(zip(b, out)) if a != z] == [pos, pos + 1]

d = r / 'compat/sheng-framework/audio-wait-v1'
d.mkdir(exist_ok=True)
(d / p.name).write_bytes(out)
record = dict(input_sha256=sha(b), output_sha256=sha(out),
              va=va, offset=pos, before='36038052', after=after.hex(),
              tries_before=25, tries_after=2, sleep_ms=200,
              wait_budget_before_ms=5000, wait_budget_after_ms=400,
              scope='Original lookup, shared lock, failure result, permissions and CFI unchanged. No fabricated audio group or device.')
(d / 'patch.json').write_text(json.dumps(record, indent=2) + '\n', encoding='utf-8')
octal = ''.join('\\%03o' % x for x in after)
lines = [
    '#!/busybox sh', 'set -eu', 'B=/busybox', 'R=/hmos-root',
    'S=$R/system/lib64/libaudio_policy_service.z.so',
    'T=$R/compat/lib64/libaudio_policy_service.z.so',
    'sum=$($B sha256sum "$S"); sum=${sum%% *}',
    f'if [ "$sum" = {sha(out)} ]; then echo AUDIO_WAIT_ALREADY_STAGED=1; exit 0; fi',
    f'[ "$sum" = {sha(b)} ] || exit 62',
    '$B cp "$S" "$T"',
    f"$B printf '{octal}' | $B dd of=\"$T\" bs=1 seek={pos} conv=notrunc 2>/dev/null",
    f"echo '{sha(out)}  '\"$T\" | $B sha256sum -c -",
    '$B chmod 0644 "$T"', '$B mount --bind "$T" "$S"',
    'echo AUDIO_VOLUME_GROUP_WAIT_400MS_STAGED=1',
]
(d / 'apply-audio-wait-v1.sh').write_text('\n'.join(lines) + '\n', encoding='utf-8', newline='\n')
print(json.dumps(record, indent=2))
