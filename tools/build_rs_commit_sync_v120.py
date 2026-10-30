"""Persist the verified client-only RS transport fix and original Web update SA."""
from pathlib import Path
import base64
import hashlib
import json
import struct
import subprocess

r = Path(__file__).resolve().parent.parent
sha = lambda b: hashlib.sha256(b).hexdigest()
d = r / 'work/rs-commit-sync-v120'
d.mkdir(exist_ok=True)
patchdir = r / 'compat/sheng-graphics/rs-commit-sync-v1'
patchdir.mkdir(exist_ok=True)
source = (r/'compat/sheng-graphics/surface-usage-v1/librender_service_base.z.so').read_bytes()
assert sha(source) == '7f4fdf74cc0897ed322af94835a76fa3f5dd8fa82f44f75f5ab47cfa7a91f57b'
va = 0x88bdb4
phoff = struct.unpack_from('<Q', source, 32)[0]
ents, num = struct.unpack_from('<HH', source, 54)
segments = [struct.unpack_from('<IIQQQQQQ', source, phoff+i*ents) for i in range(num)]
offsets = [s[2]+va-s[3] for s in segments if s[0] == 1 and s[1]&1 and s[3] <= va < s[3]+s[5]]
assert len(offsets) == 1
off = offsets[0]
guard = bytes.fromhex('e06300912100805216320194')
assert source[off-4:off+8] == guard
after = bytes.fromhex('01008052')
patched = source[:off] + after + source[off+4:]
(patchdir/'librender_service_base.z.so').write_bytes(patched)
script = '\n'.join([
    '#!/bin/sh', 'set -eu', 'B=/busybox', 'p=/hmos-root/compat/lib64/librender_service_base.z.so',
    f'echo "{sha(source)}  $p" | $B sha256sum -c -',
    '$B cp "$p" "$p.rs-sync-new"',
    f'echo {base64.b64encode(after).decode()} | $B base64 -d | $B dd of="$p.rs-sync-new" bs=1 seek={off} conv=notrunc',
    f'echo "{sha(patched)}  $p.rs-sync-new" | $B sha256sum -c -',
    '$B chmod 0644 "$p.rs-sync-new"', '$B mv "$p.rs-sync-new" "$p"',
    'echo SHENG_RS_COMMIT_SYNC_INSTALLED', ''])
(patchdir/'apply-rs-commit-sync-v1.sh').write_text(script, encoding='utf-8', newline='\n')
patch_report = dict(input_sha256=sha(source), output_sha256=sha(patched),
    function='RSClientToRenderConnectionProxy::CommitTransaction', virtual_address=hex(va),
    offset=off, guard=guard.hex(), before='21008052', after=after.hex(),
    intent='Only this client request changes TF_ASYNC to TF_SYNC; original server token/ownership checks stay intact',
    runtime_verified=True, evidence='output/screenshots/v119-aweme-sync-newapp-0608.jpeg',
    physical_user_confirmation=True, cold_boot_verified=False)
(patchdir/'manifest.json').write_text(json.dumps(patch_report, indent=2)+'\n')

def parse(b):
    pos, result = 0, {}
    while b[pos:pos+6] == b'070701':
        f = [int(b[pos+6+i*8:pos+14+i*8], 16) for i in range(13)]
        name = b[pos+110:pos+110+f[11]-1].decode()
        start = (pos+110+f[11]+3)&~3
        if name == 'TRAILER!!!': return result
        assert name not in result
        result[name] = (f, b[start:start+f[6]])
        pos = (start+f[6]+3)&~3
    raise ValueError('Invalid cpio')

def pack(entries):
    out = bytearray()
    for name, (fields, blob) in list(entries.items())+[('TRAILER!!!', ([0]*13, b''))]:
        f = fields.copy(); nb = name.encode()+b'\0'
        f[6], f[11], f[12] = len(blob), len(nb), 0
        out.extend(b'070701'+''.join(f'{v:08x}' for v in f).encode()+nb)
        out.extend(bytes((-len(out))%4)); out.extend(blob); out.extend(bytes((-len(out))%4))
    out.extend(bytes((-len(out))%512))
    return out

def regular(blob, mode=0o100755):
    return ([0, mode, 0, 0, 1, 0, len(blob), 0, 0, 0, 0, 0, 0], blob)

exe = 'C:/MIO-KITCHEN-PYSIDE6-5.0.0-PREVIEW/bin/Windows/AMD64/magiskboot.exe'
base = (r/'output/vendor_boot_hmos_compat_v119.img').read_bytes()
assert sha(base) == '80792c91465843faa2086734bd55ac3d44426d32668d27634c22ad303e66b125'
version, page = struct.unpack_from('<II', base, 8)
hs, ds = struct.unpack_from('<II', base, 2096)
ts, ne, es, bs = struct.unpack_from('<IIII', base, 2112)
assert base[:8] == b'VNDRBOOT' and (version, hs, ne) == (4, 2128, 1)
align = lambda x: (x+page-1)//page*page
rs = align(hs); ram_size = struct.unpack_from('<I', base, 24)[0]
dt = rs+align(ram_size); tt = dt+align(ds); bc = tt+align(ts)
(d/'base.lz4').write_bytes(base[rs:rs+ram_size])
subprocess.run([exe, 'decompress', str(d/'base.lz4'), str(d/'base.cpio')], check=True, capture_output=True)
old = parse((d/'base.cpio').read_bytes())
assert old == parse((r/'work/storage-local-v119/ramdisk.cpio').read_bytes())
new = dict(old); prefix = 'sheng-compat-v118/'
name = prefix+'graphics/apply-rs-commit-sync-v1.sh'
new[name] = regular(script.encode())
changed = {name}
name = prefix+'graphics/apply-render-usage.sh'
fields, original = old[name]
assert b'SHENG_RS_COMMIT_SYNC_INSTALLED' not in original and original.endswith(b'\n')
new[name] = (fields.copy(), original+b'/busybox sh /graphics/apply-rs-commit-sync-v1.sh\n')
changed.add(name)
name = prefix+'graphics/init-desktop-services.cfg'
fields, original = old[name]; cfg = json.loads(original)
assert not any(s['name'] == 'app_fwk_update_service' for s in cfg['services'])
svc = json.loads((r/'work/hmos_system/system/system/etc/init/app_fwk_update_service.cfg').read_bytes())['services'][0]
assert svc['uid'] == 'app_fwk_update' and svc['path'] == ['/system/bin/sa_main', '/system/profile/app_fwk_update_service.json']
svc.update(once=1, sandbox=0, saspawn=False)
cfg['services'].append(svc)
new[name] = (fields.copy(), (json.dumps(cfg, indent=2)+'\n').encode())
changed.add(name)
name = prefix+'graphics/native_bundle_cli'
fields, original = old[name]
new[name] = (fields.copy(), (r/'compat/debug-tools/native_bundle_system_cli').read_bytes())
assert sha(new[name][1]) == '73a8774af2c9119f5fe7808ccfdfed4c6a931463de40b2fb1074e8e10df164e8'
changed.add(name)
manifest = {n[len(prefix):]: dict(bytes=len(b), mode=oct(f[1]), sha256=sha(b))
    for n, (f, b) in new.items() if n.startswith(prefix) and n != prefix+'MANIFEST.json'}
new[prefix+'MANIFEST.json'] = regular((json.dumps(manifest, indent=2)+'\n').encode(), 0o100644)
changed.add(prefix+'MANIFEST.json')
assert set(new)-set(old) == {prefix+'graphics/apply-rs-commit-sync-v1.sh'}
assert all(new[n] == v for n, v in old.items() if n not in changed)
raw = pack(new)
normalized = parse(raw)
assert set(normalized) == set(new)
assert all(normalized[n][1] == blob and normalized[n][0][:6] == fields[:6]
           and normalized[n][0][7:11] == fields[7:11]
           for n, (fields, blob) in new.items())
new = normalized
(d/'ramdisk.cpio').write_bytes(raw)
subprocess.run([exe, 'compress=lz4_legacy', str(d/'ramdisk.cpio'), str(d/'ramdisk.lz4')], check=True, capture_output=True)
compressed = (d/'ramdisk.lz4').read_bytes()
table = bytearray(base[tt:tt+ts]); assert struct.unpack_from('<II', table) == (ram_size, 0)
struct.pack_into('<I', table, 0, len(compressed))
image = bytearray(base[:rs]); struct.pack_into('<I', image, 24, len(compressed))
for blob in [compressed, base[dt:dt+ds], table, base[bc:bc+bs]]:
    image.extend(blob); image.extend(bytes((-len(image))%page))
assert len(image) < len(base)-4096
image.extend(bytes(len(base)-len(image)))
(d/'roundtrip.lz4').write_bytes(image[rs:rs+len(compressed)])
subprocess.run([exe, 'decompress', str(d/'roundtrip.lz4'), str(d/'roundtrip.cpio')], check=True, capture_output=True)
assert parse((d/'roundtrip.cpio').read_bytes()) == new
ndt = rs+align(len(compressed)); ntt = ndt+align(ds); nbc = ntt+align(ts)
assert image[ndt:ndt+ds] == base[dt:dt+ds] and image[nbc:nbc+bs] == base[bc:bc+bs]
hdr = bytearray(image[:rs]); struct.pack_into('<I', hdr, 24, ram_size); assert hdr == base[:rs]
tab = bytearray(image[ntt:ntt+ts]); struct.pack_into('<I', tab, 0, ram_size); assert tab == base[tt:tt+ts]
out = r/'output/vendor_boot_hmos_compat_v120.img'; out.write_bytes(image)
report = dict(version='v120', status='built_not_flashed',
    vendor_boot=dict(file=out.name, bytes=len(image), sha256=sha(image)),
    init_boot_unchanged=True, payload_prefix=prefix, preserved_v119_entries=True,
    changed_entries=sorted(changed), dtb_unchanged=True, bootconfig_unchanged=True,
    cpio_verified=True, stock_vendor_modules_and_audio_unchanged=True,
    cold_boot_verified=False, rs_transport=patch_report,
    original_web_update_sa8350_registered=True, webcore_install_verified=False)
(r/'analysis/rs-commit-sync-v120-verification.json').write_text(json.dumps(report, indent=2)+'\n')
(r/'output/v120-payload-manifest.json').write_text(json.dumps(manifest, indent=2)+'\n')
print(json.dumps(report, indent=2))
