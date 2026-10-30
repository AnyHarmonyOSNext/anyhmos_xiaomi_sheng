"""Restore real, non-loading WiFi device lookup and correct WPA demand loading.

Keep the v100 vendor libraries, kernel, GPU and userdata behavior unchanged.
"""
from pathlib import Path
import hashlib
import json
import shutil
import struct
import subprocess

r = Path(__file__).resolve().parent.parent
d = r/'compat/sheng-graphics/v101'
assert not (r/'analysis/wifi-sdk-real-proxy-v1.json').exists()
if not d.exists():
    shutil.copytree(r/'compat/sheng-graphics/v100', d)
for p in list(d.iterdir()):
    if p.is_file() and p.suffix in {'.sh', '.cfg'}:
        q = p.with_name(p.name.replace('v100', 'v101'))
        content = p.read_text(encoding='utf-8').replace('v100', 'v101').replace('V100', 'V101')
        if p != q:
            p.unlink()
        q.write_text(content, encoding='utf-8', newline='\n')
for name in ['hmos_probe_v100.c', 'probe_graphics_v100.inc', 'probe_command_v100.inc',
             'build_probe_v100.py', 'verify_v100.py', 'start_native_desktop_v100.sh']:
    (r/'tools'/name.replace('v100', 'v101')).write_text(
        (r/'tools'/name).read_text(encoding='utf-8').replace('v100', 'v101'),
        encoding='utf-8', newline='\n')
(r/'tools/configs/init-core-v101.cfg').write_text(
    (r/'tools/configs/init-core-v100.cfg').read_text().replace('v100', 'v101'), newline='\n')

# Original code, with two reviewed instructions changed. Keep all donor proxy
# creation, reference counting, permission checks, PAC and CFI checks intact.
source = r/'work/hmos_system/system/system/lib64/platformsdk/libwifi_sdk.z.so'
original = source.read_bytes()
assert hashlib.sha256(original).hexdigest() == '06765b1a54ac5c861baf5902f9081bb7da93a3b6765ae53085e150d3d7a00368'
patched = bytearray(original)
phoff = struct.unpack_from('<Q', original, 32)[0]
phsize, phnum = struct.unpack_from('<HH', original, 54)
def file_offset(va):
    for i in range(phnum):
        kind, flags, off, addr, paddr, filesz, memsz, align = struct.unpack_from('<IIQQQQQQ', original, phoff+i*phsize)
        if kind == 1 and addr <= va and va+4 <= addr+filesz:
            return off+va-addr
    raise ValueError(hex(va))
changes = [
    # ISystemAbilityManager vtable: slot4 GetSystemAbility -> slot5 CheckSystemAbility.
    (0x4e6e8, 'c91240f9', 'c91640f9', 'Query an already published SA without waiting for demand loading'),
    # In the original null-remote error path x23 was initialized at 0x4e8e4.
    # Skip LoadWifiSa and its retry; retain the original logged false return.
    (0x4e904, '2fc80094', struct.pack('<I', 0x14000000 | ((0x4e970-0x4e904)//4)).hex(),
     'Absent service returns the original failure without synchronous LoadWifiSa'),
]
for va, before, after, reason in changes:
    offset = file_offset(va)
    assert original[offset:offset+4].hex() == before, (hex(offset), original[offset:offset+4].hex())
    patched[offset:offset+4] = bytes.fromhex(after)
entry = file_offset(0x4e628)
assert original[entry:entry+8].hex() == 'ef0100d0ef1141f9'
(d/'libwifi_sdk.z.so').write_bytes(patched)
manifest = {
    'name': 'donor-wifi-device-nonloading-real-proxy-v1',
    'input_sha256': hashlib.sha256(original).hexdigest(),
    'output_sha256': hashlib.sha256(patched).hexdigest(),
    'guards': [{'offset': entry, 'bytes': 'ef0100d0ef1141f9'}],
    'changes': [dict(va=hex(o), offset=file_offset(o), before=b, after=a, reason=t) for o,b,a,t in changes],
    'scope': 'Only GetWifiDeviceProxy: original real proxy or original failure; no successful network state fabricated',
    'vendor_modified': False,
}
(r/'analysis/wifi-sdk-real-proxy-v1.json').write_text(json.dumps(manifest, indent=2)+'\n')

hcs = (r/'tools/configs/sheng-graphics-v100.hcs').read_text()
marker = 'serviceName = "wpa_interface_service";\n                    preload = 1;'
assert hcs.count(marker) == 1
# DEVICE_PRELOAD_DISABLE=2 makes LoadDevice find this device in dynamicDevInfos.
# With preload1 it is absent from that list and returns HDF_DEV_ERR_NO_DEVICE=-202.
hcs = hcs.replace(marker, marker.replace('preload = 1', 'preload = 2'))
(r/'tools/configs/sheng-graphics-v101.hcs').write_text(hcs, newline='\n')
w = '/mnt/c/SHENG_WORKSPACE'
subprocess.run(['wsl', '-d', 'Ubuntu-22.04', '--', '/root/hmos-work/graphics-deps/hc-gen',
                '-o', w+'/compat/sheng-graphics/v101/hdf_default.hcb',
                w+'/tools/configs/sheng-graphics-v101.hcs'], check=True)
p = r/'tools/verify_v101.py'
v = p.read_text()
marker = " assert b'chip_interface_service' in new['hmos-hdf-graphics.hcb'][1]"
assert v.count(marker) == 1
v = v.replace(marker, marker+"\n assert hashlib.sha256(new['graphics/libwifi_sdk.z.so'][1]).hexdigest()=='"+manifest['output_sha256']+"'")
p.write_text(v, newline='\n')
print(json.dumps(manifest, indent=2))
