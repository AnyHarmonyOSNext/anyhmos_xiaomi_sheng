"""Use the donor audio policy client's existing nonblocking SA branch."""
from pathlib import Path
import hashlib
import json
import shutil
import struct

r = Path(__file__).resolve().parent.parent
for n in ['hmos_probe.c', 'probe_graphics.inc', 'probe_command.inc']:
    p = r / 'tools' / n
    q = r / 'tools/archive' / (p.stem + '_v65' + p.suffix)
    if not q.exists():
        shutil.copy2(p, q)
d = r / 'compat/sheng-graphics/v66'
assert not d.exists()
shutil.copytree(r / 'compat/sheng-graphics/v65', d)
shutil.copy2(r / 'tools/configs/init-core-v65.cfg', r / 'tools/configs/init-core-v66.cfg')
src = r / 'work/hmos_system/system/system/lib64/platformsdk/libaudio_policy_client.z.so'
b = src.read_bytes()
assert hashlib.sha256(b).hexdigest() == '38e59767cb5d9c2d1e7cf895efb68ecaeedc1fc1f12284d9e63f6f3544f3da1d'
va = 0x3b604
phoff = struct.unpack_from('<Q', b, 32)[0]
phsize, phnum = struct.unpack_from('<HH', b, 54)
offset = None
for i in range(phnum):
    kind, flags, off, addr, _, filesz, _, _ = struct.unpack_from('<IIQQQQQQ', b, phoff + i * phsize)
    if kind == 1 and addr <= va and va + 4 <= addr + filesz:
        offset = off + va - addr
assert offset is not None
old = bytes.fromhex('80020012')  # and w0,w20,#1
assert b[offset:offset + 4] == old
out = bytearray(b)
out[offset:offset + 4] = bytes.fromhex('00008052')  # mov w0,#0
(d / src.name).write_bytes(out)
report = {'function': 'AudioPolicyManager::GetAudioPolicyManagerProxy(bool)',
          'va': hex(va), 'file_offset': offset, 'old': old.hex(),
          'new': out[offset:offset + 4].hex(),
          'branch': '0x3b800 tbz w20,#0 -> 0x3b85c, vtable+40 check SA3009',
          'semantics': 'reuse nonblocking query; existing service stays usable, absent service returns original null/error paths',
          'input_sha256': hashlib.sha256(b).hexdigest(),
          'output_sha256': hashlib.sha256(out).hexdigest(),
          'restored_v65_loopback_function': True, 'vendor_modified': False}
(r / 'analysis/v66-audio-nonblocking-patch.json').write_text(json.dumps(report, indent=2) + '\n')
p = r / 'tools/probe_graphics.inc'
p.write_text(p.read_text().replace('SYSTEM_AUDIO_LOOPBACK_COMPAT_BIND: unavailable capability returns false',
                                 'SYSTEM_AUDIO_POLICY_COMPAT_BIND: original nonblocking query for SA3009'))
p = r / 'tools/hmos_probe.c'
p.write_text(p.read_text().replace('v65', 'v66'))
for n in ['build_probe', 'verify']:
    (r / f'tools/{n}_v66.py').write_text((r / f'tools/{n}_v65.py').read_text().replace('v65', 'v66'))
print(json.dumps(report, indent=2))
