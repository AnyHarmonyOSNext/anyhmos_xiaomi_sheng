"""Disable only unsupported audio loopback capability while audio is absent."""
from pathlib import Path
import hashlib
import json
import shutil
import struct

r = Path(__file__).resolve().parent.parent
for n in ['hmos_probe.c', 'probe_graphics.inc', 'probe_command.inc']:
    p = r / 'tools' / n
    q = r / 'tools/archive' / (p.stem + '_v64' + p.suffix)
    if not q.exists():
        shutil.copy2(p, q)
d = r / 'compat/sheng-graphics/v65'
assert not d.exists()
shutil.copytree(r / 'compat/sheng-graphics/v64', d)
shutil.copy2(r / 'tools/configs/init-core-v64.cfg', r / 'tools/configs/init-core-v65.cfg')
src = r / 'work/hmos_system/system/system/lib64/platformsdk/libaudio_policy_client.z.so'
b = src.read_bytes()
assert hashlib.sha256(b).hexdigest() == '38e59767cb5d9c2d1e7cf895efb68e.caeedc1fc1f12284d9e63f6f3544f3da1d'.replace('.', '')
va = 0x52b8c
phoff = struct.unpack_from('<Q', b, 32)[0]
phsize, phnum = struct.unpack_from('<HH', b, 54)
offset = None
for i in range(phnum):
    kind, flags, off, addr, _, filesz, _, _ = struct.unpack_from('<IIQQQQQQ', b, phoff + i * phsize)
    if kind == 1 and addr <= va and va + 8 <= addr + filesz:
        offset = off + va - addr
assert offset is not None
old = bytes.fromhex('af0100f0efb942f9')
assert b[offset:offset + 8] == old
# The original null-proxy path at 0x52c44 returns w19=0, then w0=w19.
# Return the same boolean false before any PAC/stack or blocking SA lookup.
out = bytearray(b)
out[offset:offset + 8] = bytes.fromhex('00008052c0035fd6')
(d / src.name).write_bytes(out)
report = {'function': 'OHOS::AudioStandard::AudioPolicyManager::IsAudioLoopbackSupported',
          'va': hex(va), 'file_offset': offset, 'old': old.hex(),
          'new': out[offset:offset + 8].hex(), 'absent_proxy_false_branch': '0x52c44',
          'input_sha256': hashlib.sha256(b).hexdigest(),
          'output_sha256': hashlib.sha256(out).hexdigest(),
          'build_id': 'beb83455e721d802848366bcee12afeb',
          'semantics': 'audio loopback unavailable; no successful audio operation',
          'vendor_modified': False}
(r / 'analysis/v65-audio-loopback-patch.json').write_text(json.dumps(report, indent=2) + '\n')
p = r / 'tools/probe_graphics.inc'
s = p.read_text()
mark = '    note("SYSTEM_WIFI_SDK_COMPAT_BIND: absent device proxy returns false; vendor untouched");'
assert s.count(mark) == 1
s = s.replace(mark, mark + '\n    if(copy_ram_asset("/graphics/libaudio_policy_client.z.so","/hmos-root/compat/lib64/libaudio_policy_client.z.so",0644)<0)return -1;\n    if(mount("/hmos-root/compat/lib64/libaudio_policy_client.z.so","/hmos-root/system/lib64/platformsdk/libaudio_policy_client.z.so",NULL,MS_BIND,NULL)<0)return -1;\n    note("SYSTEM_AUDIO_LOOPBACK_COMPAT_BIND: unavailable capability returns false; vendor untouched");')
p.write_text(s)
p = r / 'tools/hmos_probe.c'
p.write_text(p.read_text().replace('v64', 'v65'))
for n in ['build_probe', 'verify']:
    (r / f'tools/{n}_v65.py').write_text((r / f'tools/{n}_v64.py').read_text().replace('v64', 'v65'))
print(json.dumps(report, indent=2))
