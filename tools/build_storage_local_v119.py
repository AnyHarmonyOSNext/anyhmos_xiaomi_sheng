"""Add native local-storage selection to validated v118 vendor_boot only."""
from pathlib import Path
import hashlib
import json
import struct
import subprocess

r = Path(__file__).resolve().parent.parent
d = r / 'work/storage-local-v119'
d.mkdir(exist_ok=True)
exe = 'C:/MIO-KITCHEN-PYSIDE6-5.0.0-PREVIEW/bin/Windows/AMD64/magiskboot.exe'
sha = lambda b: hashlib.sha256(b).hexdigest()
prefix = 'sheng-compat-v118/'  # Keep the validated generic entry unchanged.


def parse(b):
    pos, result = 0, {}
    while b[pos:pos+6] == b'070701':
        fields = [int(b[pos+6+i*8:pos+14+i*8], 16) for i in range(13)]
        name = b[pos+110:pos+110+fields[11]-1].decode()
        start = (pos+110+fields[11]+3) & ~3
        if name == 'TRAILER!!!':
            return result
        assert name not in result
        result[name] = (fields, b[start:start+fields[6]])
        pos = (start+fields[6]+3) & ~3
    raise ValueError('Invalid cpio')


def pack(entries):
    out = bytearray()
    for name, (fields, data) in list(entries.items()) + [('TRAILER!!!', ([0]*13, b''))]:
        fields = fields.copy()
        nb = name.encode() + b'\0'
        fields[6], fields[11], fields[12] = len(data), len(nb), 0
        out.extend(b'070701' + ''.join(f'{x:08x}' for x in fields).encode() + nb)
        out.extend(bytes((-len(out)) % 4))
        out.extend(data)
        out.extend(bytes((-len(out)) % 4))
    out.extend(bytes((-len(out)) % 512))
    return out


def regular(blob, mode=0o100755):
    return ([0, mode, 0, 0, 1, 0, len(blob), 0, 0, 0, 0, 0, 0], blob)


base = (r / 'output/vendor_boot_hmos_compat_v118.img').read_bytes()
assert sha(base) == '203a002eb24a75dd8828e9d0b01d84c2d3d91054c1c0f5ba56bbd06c45de6b8e'
assert base[:8] == b'VNDRBOOT'
version, page = struct.unpack_from('<II', base, 8)
hs, ds = struct.unpack_from('<II', base, 2096)
ts, ne, es, bs = struct.unpack_from('<IIII', base, 2112)
assert (version, hs, ne) == (4, 2128, 1)
align = lambda x: (x+page-1)//page*page
rs = align(hs)
ram_size = struct.unpack_from('<I', base, 24)[0]
dt = rs + align(ram_size)
tt = dt + align(ds)
bc = tt + align(ts)
(d / 'base.lz4').write_bytes(base[rs:rs+ram_size])
subprocess.run([exe, 'decompress', str(d/'base.lz4'), str(d/'base.cpio')], check=True, capture_output=True)
old = parse((d/'base.cpio').read_bytes())
assert old == parse((r/'work/vendor-migration-v118/ramdisk.cpio').read_bytes())
new = dict(old)
script = (r/'compat/sheng-framework/storage-local-v1/apply-storage-local-v1.sh').read_bytes()
assert b'\r' not in script
new[prefix+'graphics/apply-storage-local-v1.sh'] = regular(script)
name = prefix+'graphics/apply-msdp-local-v1.sh'
fields, original = old[name]
assert original.count(b'set -eu\n') == 1
new[name] = (fields.copy(), original.replace(b'set -eu\n', b'set -eu\n/busybox sh /graphics/apply-storage-local-v1.sh\n', 1))
manifest = {}
for name, (fields, blob) in new.items():
    if name.startswith(prefix) and name != prefix+'MANIFEST.json':
        manifest[name[len(prefix):]] = dict(bytes=len(blob), mode=oct(fields[1]), sha256=sha(blob))
new[prefix+'MANIFEST.json'] = regular((json.dumps(manifest, indent=2)+'\n').encode(), 0o100644)
allowed = {prefix+'graphics/apply-storage-local-v1.sh', prefix+'graphics/apply-msdp-local-v1.sh', prefix+'MANIFEST.json'}
assert set(new)-set(old) == {prefix+'graphics/apply-storage-local-v1.sh'}
assert all(new[k] == v for k, v in old.items() if k not in allowed)
raw = pack(new)
new = parse(raw)
(d/'ramdisk.cpio').write_bytes(raw)
subprocess.run([exe, 'compress=lz4_legacy', str(d/'ramdisk.cpio'), str(d/'ramdisk.lz4')], check=True, capture_output=True)
compressed = (d/'ramdisk.lz4').read_bytes()
table = bytearray(base[tt:tt+ts])
assert struct.unpack_from('<II', table) == (ram_size, 0)
struct.pack_into('<I', table, 0, len(compressed))
image = bytearray(base[:rs])
struct.pack_into('<I', image, 24, len(compressed))
for blob in [compressed, base[dt:dt+ds], table, base[bc:bc+bs]]:
    image.extend(blob)
    image.extend(bytes((-len(image)) % page))
assert len(image) < len(base)-4096
image.extend(bytes(len(base)-len(image)))
out = r/'output/vendor_boot_hmos_compat_v119.img'
out.write_bytes(image)
# Independent round trip and container preservation checks.
(d/'roundtrip.lz4').write_bytes(image[rs:rs+len(compressed)])
subprocess.run([exe, 'decompress', str(d/'roundtrip.lz4'), str(d/'roundtrip.cpio')], check=True, capture_output=True)
assert parse((d/'roundtrip.cpio').read_bytes()) == new
ndt = rs+align(len(compressed))
ntt = ndt+align(ds)
nbc = ntt+align(ts)
assert image[ndt:ndt+ds] == base[dt:dt+ds]
assert image[nbc:nbc+bs] == base[bc:bc+bs]
header = bytearray(image[:rs]); struct.pack_into('<I', header, 24, ram_size)
assert header == base[:rs]
tablecheck = bytearray(image[ntt:ntt+ts]); struct.pack_into('<I', tablecheck, 0, ram_size)
assert tablecheck == base[tt:tt+ts]
init = r/'output/init_boot_hmos_entry_v118.img'
assert sha(init.read_bytes()) == '6f3eb88aa1422f6ed114f58c0e32e991b01b9ab3fa96c386626434891e215ef9'
report = dict(version='v119', status='built_not_flashed',
              vendor_boot=dict(file=out.name, bytes=len(image), sha256=sha(image)),
              init_boot_unchanged=True, payload_prefix=prefix, preserved_v118_entries=True,
              changed_entries=sorted(allowed), dtb_unchanged=True, bootconfig_unchanged=True,
              stock_vendor_modules_and_audio_unchanged=True, cpio_verified=True,
              basis='AnyHarmonyOS devices/oneplus-ace5/boot/tools/build.py native LocalMount selection; sheng boot error13600721 errno19',
              cold_boot_verified=False, account_unlock_verified=False, thirdparty_launch_verified=False)
(r/'analysis/storage-local-v119-verification.json').write_text(json.dumps(report, indent=2)+'\n')
(r/'output/v119-payload-manifest.json').write_text(json.dumps(manifest, indent=2)+'\n')
print(json.dumps(report, indent=2))
