"""Preserve v120 payload; replace only the diagnostic collector and manifest."""
from pathlib import Path
import hashlib
import json
import struct
import subprocess

r = Path(__file__).resolve().parent.parent
sha = lambda b: hashlib.sha256(b).hexdigest()
d = r/'work/usb-session-v121'
d.mkdir(exist_ok=True)
cmd = ('cd "/mnt/c/SHENG_WORKSPACE" && '
       'gcc -O2 -Wall -Wextra -Werror tools/test_probe_serial_v121.c -o /tmp/test_probe_serial_v121 && '
       '/tmp/test_probe_serial_v121 && '
       'aarch64-linux-gnu-gcc -static -O2 -Wall -Wextra -Werror tools/hmos_probe_v121.c -o work/hmos_probe_v121 && '
       'aarch64-linux-gnu-strip work/hmos_probe_v121')
subprocess.run(['wsl','-d','Ubuntu-22.04','--','bash','-lc',cmd],check=True)

def parse(b):
    pos, result = 0, {}
    while b[pos:pos+6] == b'070701':
        f = [int(b[pos+6+i*8:pos+14+i*8],16) for i in range(13)]
        n = b[pos+110:pos+109+f[11]].decode()
        start = (pos+110+f[11]+3)&~3
        if n == 'TRAILER!!!': return result
        assert n not in result
        result[n] = (f,b[start:start+f[6]])
        pos = (start+f[6]+3)&~3
    raise ValueError('Invalid cpio')

def pack(entries):
    out = bytearray()
    for name,(fields,blob) in list(entries.items())+[('TRAILER!!!',([0]*13,b''))]:
        f = fields.copy(); nb = name.encode()+b'\0'
        f[6],f[11],f[12] = len(blob),len(nb),0
        out.extend(b'070701'+''.join(f'{v:08x}' for v in f).encode()+nb)
        out.extend(bytes((-len(out))%4));out.extend(blob);out.extend(bytes((-len(out))%4))
    out.extend(bytes((-len(out))%512));return out

exe = 'C:/MIO-KITCHEN-PYSIDE6-5.0.0-PREVIEW/bin/Windows/AMD64/magiskboot.exe'
base = (r/'output/vendor_boot_hmos_compat_v120.img').read_bytes()
assert sha(base) == '7f9f2d398016e2aff418918efe3ecf0dbe54976beb074dc6ff909db04e09899a'
version,page = struct.unpack_from('<II',base,8)
hs,ds = struct.unpack_from('<II',base,2096)
ts,ne,es,bs = struct.unpack_from('<IIII',base,2112)
assert base[:8] == b'VNDRBOOT' and (version,hs,ne) == (4,2128,1)
align = lambda x:(x+page-1)//page*page
rs = align(hs);ram_size = struct.unpack_from('<I',base,24)[0]
dt = rs+align(ram_size);tt = dt+align(ds);bc = tt+align(ts)
(d/'base.lz4').write_bytes(base[rs:rs+ram_size])
subprocess.run([exe,'decompress',str(d/'base.lz4'),str(d/'base.cpio')],check=True,capture_output=True)
old = parse((d/'base.cpio').read_bytes())
assert old == parse((r/'work/rs-commit-sync-v120/roundtrip.cpio').read_bytes())
new = dict(old);prefix = 'sheng-compat-v118/'
name = prefix+'hmos-probe';fields,original = old[name]
assert sha(original) == '50e16d7b19c7741d580eda6a04ba33955c0028f732f1a316aabee4c467a7586f'
binary = (r/'work/hmos_probe_v121').read_bytes()
assert b'USB-session recovery' in binary and b'USB session reset' in binary
new[name] = (fields.copy(),binary)
manifest = {n[len(prefix):]:dict(bytes=len(b),mode=oct(f[1]),sha256=sha(b))
            for n,(f,b) in new.items() if n.startswith(prefix) and n!=prefix+'MANIFEST.json'}
name = prefix+'MANIFEST.json';fields,_ = old[name]
new[name] = (fields.copy(),(json.dumps(manifest,indent=2)+'\n').encode())
allowed = {prefix+'hmos-probe',prefix+'MANIFEST.json'}
assert set(new) == set(old)
assert all(new[n]==v for n,v in old.items() if n not in allowed)
raw = pack(new);new = parse(raw)
(d/'ramdisk.cpio').write_bytes(raw)
subprocess.run([exe,'compress=lz4_legacy',str(d/'ramdisk.cpio'),str(d/'ramdisk.lz4')],check=True,capture_output=True)
compressed = (d/'ramdisk.lz4').read_bytes()
table = bytearray(base[tt:tt+ts]);assert struct.unpack_from('<II',table)==(ram_size,0)
struct.pack_into('<I',table,0,len(compressed))
image = bytearray(base[:rs]);struct.pack_into('<I',image,24,len(compressed))
for blob in [compressed,base[dt:dt+ds],table,base[bc:bc+bs]]:
    image.extend(blob);image.extend(bytes((-len(image))%page))
assert len(image)<len(base)-4096
image.extend(bytes(len(base)-len(image)))
(d/'roundtrip.lz4').write_bytes(image[rs:rs+len(compressed)])
subprocess.run([exe,'decompress',str(d/'roundtrip.lz4'),str(d/'roundtrip.cpio')],check=True,capture_output=True)
assert parse((d/'roundtrip.cpio').read_bytes())==new
ndt=rs+align(len(compressed));ntt=ndt+align(ds);nbc=ntt+align(ts)
assert image[ndt:ndt+ds]==base[dt:dt+ds] and image[nbc:nbc+bs]==base[bc:bc+bs]
hdr=bytearray(image[:rs]);struct.pack_into('<I',hdr,24,ram_size);assert hdr==base[:rs]
tab=bytearray(image[ntt:ntt+ts]);struct.pack_into('<I',tab,0,ram_size);assert tab==base[tt:tt+ts]
out=r/'output/vendor_boot_hmos_compat_v121.img';out.write_bytes(image)
report=dict(version='v121',status='built_not_flashed',
    vendor_boot=dict(file=out.name,bytes=len(image),sha256=sha(image)),
    probe=dict(bytes=len(binary),sha256=sha(binary)),cpio_verified=True,
    init_boot_unchanged=True,preserved_v120_entries=True,changed_entries=sorted(allowed),
    dtb_unchanged=True,bootconfig_unchanged=True,stock_vendor_modules_and_audio_unchanged=True,
    pty_disconnect_reopen_verified=True,cold_boot_verified=False,usb_cold_boot_reconnect_verified=False,
    purpose='recover tty EOF/EIO/POLLHUP, raw -HUPCL, discard partial stale input, bound kmsg drain',
    device_disconnect_cause='not proven; no tty error telemetry in old binary')
(r/'analysis/usb-session-v121-verification.json').write_text(json.dumps(report,indent=2)+'\n')
(r/'output/v121-payload-manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
print(json.dumps(report,indent=2))
