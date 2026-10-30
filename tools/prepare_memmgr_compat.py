"""Disable only donor Hyperhold startup, keeping real native MemMgr IPC.

The upstream service places this block under USE_HYPERHOLD_MEMORY. The sheng
kernel lacks Huawei's memory.app_score/name/reclaim-ratio interfaces. This
patch skips that optional block; it does not force an IPC result to success.
"""
from pathlib import Path
import hashlib
import json
import struct

r = Path(__file__).resolve().parent.parent
d = r / 'compat/sheng-framework/memmgr-v1'
d.mkdir(exist_ok=True)
b = (r / 'work/hmos_system/system/system/lib64/libmemmgrservice.z.so').read_bytes()
assert b[:6] == b'\x7fELF\x02\x01'
phoff = struct.unpack_from('<Q', b, 32)[0]
phsize, phnum = struct.unpack_from('<HH', b, 54)
def offset(va):
    for i in range(phnum):
        typ, flags, off, addr, _, filesz, _, _ = struct.unpack_from('<II6Q', b, phoff + i * phsize)
        if typ == 1 and addr <= va < addr + filesz:
            return va - addr + off
    raise ValueError(hex(va))

va = 0x199f70
off = offset(va)
before = bytes.fromhex('32130194')  # bl ReclaimStrategyManager::GetInstance
after = bytes.fromhex('03000014')   # b 0x199f7c, past GetInstance/Init/failure branch
guards = {offset(0x199f64): 'b98200945a840094e0080036',
          offset(0x199f74): '0c15019400090036',
          offset(0x199f7c): '689ffe9747aefe970800403988090035',
          offset(0x19a098): '280500d0a6f3ffb0c6ac2391d5ffff17'}
assert b[off:off+4] == before
for pos, val in guards.items():
    assert b[pos:pos+len(bytes.fromhex(val))] == bytes.fromhex(val), hex(pos)
patched = b[:off] + after + b[off+4:]
sha = lambda x: hashlib.sha256(x).hexdigest()
manifest = {'input_sha256': sha(b), 'output_sha256': sha(patched), 'bytes': len(b),
            'changes': [{'va': va, 'offset': off, 'before': before.hex(), 'after': after.hex()}],
            'guards': [{'offset': pos, 'bytes': val} for pos, val in guards.items()],
            'upstream_reference': 'openharmony/resourceschedule_memmgr@ae0095521ed66344c08ebf8a588b9a254ede9704/services/memmgrservice/src/mem_mgr_service.cpp',
            'scope': 'Skip optional USE_HYPERHOLD_MEMORY ReclaimStrategyManager init on unsupported stock kernel. Native IPC, permission checks, priority manager and queries remain.'}
(d / 'libmemmgrservice.z.so').write_bytes(patched)
(d / 'patch.json').write_text(json.dumps(manifest, indent=2) + '\n', encoding='utf-8')
octal = ''.join('\\%03o' % x for x in after)
script = f'''#!/busybox sh
set -eu
B=/busybox
R=/hmos-root
S=$R/system/lib64/libmemmgrservice.z.so
T=$R/compat/lib64/libmemmgrservice.z.so
sum=$($B sha256sum "$S"); sum=${{sum%% *}}
if [ "$sum" = {sha(patched)} ]; then echo MEMMGR_NATIVE_PORT_ALREADY_STAGED=1; exit 0; fi
[ "$sum" = {sha(b)} ] || exit 62
$B cp "$S" "$T"
$B printf '{octal}' | $B dd of="$T" bs=1 seek={off} conv=notrunc 2>/dev/null
echo '{sha(patched)}  '"$T" | $B sha256sum -c -
$B chmod 0644 "$T"
$B mount --bind "$T" "$S"
echo '{sha(patched)}  '"$S" | $B sha256sum -c -
echo MEMMGR_NATIVE_PORT_STAGED_UNSUPPORTED_HYPERHOLD_DISABLED=1
'''
(d / 'apply-memmgr-v1.sh').write_text(script, encoding='utf-8', newline='\n')
print(json.dumps(manifest, indent=2))
