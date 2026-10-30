"""Skip optional MSDP distributed startup; retain its real local IPC handlers."""
from pathlib import Path
import hashlib
import json
import struct

r = Path(__file__).resolve().parent.parent
src = r / 'work/msdp-v116-original/libdevicestatus_service.z.so'
b = src.read_bytes()
sha = lambda data: hashlib.sha256(data).hexdigest()
assert sha(b) == '483742fb4249e79319565814dab375b3db0ddd71de9995f99b5e254b3b2dfd69'
phoff = struct.unpack_from('<Q', b, 32)[0]
phsize, phnum = struct.unpack_from('<HH', b, 54)

def offset(va):
    for i in range(phnum):
        typ, flags, off, addr, _, size, _, _ = struct.unpack_from('<II6Q', b, phoff + i*phsize)
        if typ == 1 and addr <= va < addr + size:
            return off + va - addr
    raise ValueError(hex(va))

patched = bytearray(b)
changes = []
for va, target, name in [(0x7fee0, 0x804b0, 'EnableDSoftbus'), (0x7fef4, 0x80654, 'EnableDDM')]:
    off = offset(va)
    ins = struct.unpack_from('<I', b, off)[0]
    assert ins >> 26 == 0b100101
    imm = ins & 0x3ffffff
    if imm & (1 << 25):
        imm -= 1 << 26
    assert va + 4*imm == target
    assert b[offset(target):offset(target)+4] == bytes.fromhex('7f2303d5')  # pacibsp
    before = b[off:off+4]
    after = bytes.fromhex('1f2003d5')  # nop; both callees return void
    patched[off:off+4] = after
    changes.append(dict(va=va, offset=off, before=before.hex(), after=after.hex(),
                        callee_va=target, callee=name,
                        context=b[off-16:off+20].hex()))

assert len(patched) == len(b)
assert sum(x != y for x,y in zip(b,patched)) <= 8
d = r / 'compat/sheng-framework/msdp-local-v1'
d.mkdir(exist_ok=True)
(d/'libdevicestatus_service.z.so').write_bytes(patched)
manifest = dict(input_sha256=sha(b), output_sha256=sha(patched), bytes=len(b), changes=changes,
                scope='OnStart omits optional distributed-device/SoftBus startup. Real local drag, input IPC, permissions and replies remain.',
                evidence='output/logs/latency-v116-binder-stall-2245.txt.gz: SceneBoard -> MSDP code 0x2f waits >1s; MSDP DDM startup retries block its worker.',
                reference='openharmony/msdp_device_status OpenHarmony-6.0-Release services/native/src/devicestatus_service.cpp')
(d/'patch.json').write_text(json.dumps(manifest,indent=2)+'\n',encoding='utf-8')
script = ['#!/busybox sh','set -eu','B=/busybox','R=/hmos-root',
          'S=$R/system/lib64/libdevicestatus_service.z.so',
          'T=$R/compat/lib64/libdevicestatus_service.z.so',
          'sum=$($B sha256sum "$S"); sum=${sum%% *}',
          f'if [ "$sum" = {sha(patched)} ]; then echo MSDP_LOCAL_ALREADY_STAGED=1; exit 0; fi',
          f'[ "$sum" = {sha(b)} ] || exit 62',
          '$B cp "$S" "$T"']
for c in changes:
    octal=''.join('\\%03o'%x for x in bytes.fromhex(c['after']))
    script.append(f"$B printf '{octal}' | $B dd of=\"$T\" bs=1 seek={c['offset']} conv=notrunc 2>/dev/null")
script.extend([f'echo "{sha(patched)}  $T" | $B sha256sum -c -',
               '$B chmod 0644 "$T"', '$B mount --bind "$T" "$S"',
               f'echo "{sha(patched)}  $S" | $B sha256sum -c -',
               'echo MSDP_LOCAL_NATIVE_IPC_STAGED_OPTIONAL_DISTRIBUTED_STARTUP_DISABLED=1'])
(d/'apply-msdp-local-v1.sh').write_text('\n'.join(script)+'\n',encoding='utf-8',newline='\n')
print(json.dumps(manifest,indent=2))
