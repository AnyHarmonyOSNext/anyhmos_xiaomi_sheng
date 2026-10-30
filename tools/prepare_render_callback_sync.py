"""Exact-donor, client-only acknowledged screen callback transport experiment."""
from pathlib import Path
import hashlib, json, struct

root = Path(__file__).resolve().parent.parent
source = root / 'work/donor-hdi-link/librender_service_base.z.so'
raw = source.read_bytes()
sha = lambda b: hashlib.sha256(b).hexdigest()
assert sha(raw) == '0a699e2317dab4699117a90e7e21d5727bd823e3474a70ebaed4d32667e519ff'
assert raw[:6] == b'\x7fELF\x02\x01'
va = 0x89d798
phoff = struct.unpack_from('<Q', raw, 32)[0]
phsize, phnum = struct.unpack_from('<HH', raw, 54)
matches = []
for n in range(phnum):
    typ, flags, off, addr, _, size, _, _ = struct.unpack_from('<IIQQQQQQ', raw, phoff+n*phsize)
    if typ == 1 and addr <= va < addr+size:
        assert flags & 1
        matches.append(off+va-addr)
assert len(matches) == 1
offset = matches[0]
guard = bytes.fromhex('e0830091210080529deb0094800240f9')
assert raw[offset-4:offset+12] == guard
assert raw[offset:offset+4] == bytes.fromhex('21008052')
patched = raw[:offset]+bytes.fromhex('01008052')+raw[offset+4:]
dest = root/'compat/sheng-graphics/render-callback-sync-v1'
dest.mkdir(parents=True, exist_ok=True)
(dest/source.name).write_bytes(patched)
report = dict(name='sheng-render-callback-sync-v1', input_sha256=sha(raw), output_sha256=sha(patched),
    function='RSClientToServiceConnectionProxy::SetScreenChangeCallback', virtual_address=hex(va),
    file_offset=offset, before='21008052', after='01008052', guard_offset=offset-4, guard=guard.hex(),
    intent='TF_ASYNC to TF_SYNC for code 20480; no server/caller/token checks changed',
    reference='AnyHarmonyOS cb1ce16 render-caller-pid concept; reference input hash/offset deliberately not reused',
    official_source='graphic_graphic_2d c19cedf62fefde6bf184aa815feeaf0346aa4d49 proxy line 1000',
    status='built, not device-tested')
(dest/'manifest.json').write_text(json.dumps(report, indent=2)+'\n')
(root/'analysis/render-callback-sync-build.json').write_text(json.dumps(report, indent=2)+'\n')
print(json.dumps(report, indent=2))
