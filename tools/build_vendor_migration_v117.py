"""Move v116 payload to an additive vendor ramdisk prefix, preserve stock entries."""
from pathlib import Path
import hashlib, json, struct, subprocess

r = Path(__file__).resolve().parent.parent
exe = 'C:/MIO-KITCHEN-PYSIDE6-5.0.0-PREVIEW/bin/Windows/AMD64/magiskboot.exe'
stock = Path('E:/SHENG_STOCK_303/images')
d = r / 'work/vendor-migration-v117'
d.mkdir(exist_ok=True)
prefix = 'sheng-compat-v117/'
sha = lambda b: hashlib.sha256(b).hexdigest()

def parse(b):
    pos, out = 0, {}
    while b[pos:pos+6] == b'070701':
        f = [int(b[pos+6+i*8:pos+14+i*8], 16) for i in range(13)]
        name = b[pos+110:pos+110+f[11]-1].decode()
        start = (pos+110+f[11]+3)&~3
        if name == 'TRAILER!!!': return out
        assert name not in out, name
        out[name] = (f, b[start:start+f[6]])
        pos = (start+f[6]+3)&~3
    raise ValueError('Invalid cpio')

def pack(entries):
    out = bytearray()
    for name, (fields, blob) in list(entries.items()) + [('TRAILER!!!', ([0]*13, b''))]:
        f = fields.copy(); nb = name.encode()+b'\0'
        f[6], f[11], f[12] = len(blob), len(nb), 0
        out.extend(b'070701'+''.join(f'{v:08x}' for v in f).encode()+nb)
        out.extend(bytes((-len(out))%4)); out.extend(blob); out.extend(bytes((-len(out))%4))
    out.extend(bytes((-len(out))%512))
    return out

def regular(blob, mode=0o100755):
    return ([0, mode, 0, 0, 1, 0, len(blob), 0, 0, 0, 0, 0, 0], blob)

src = (r/'tools/hmos_probe_v116.c').read_text(encoding='utf-8')
src = src.replace('#include "probe_graphics_v116.inc"', '#include "probe_graphics_v117.inc"')
src = src.replace('sheng HMOS probe v116 --', 'sheng HMOS probe v117 vendor_boot payload --')
(r/'tools/hmos_probe_v117.c').write_text(src, encoding='utf-8', newline='\n')
inc = (r/'tools/probe_graphics_v116.inc').read_text(encoding='utf-8')
marker = '    if(graphics_run_script("/graphics/apply-preload.sh")<0)return -1;'
assert inc.count(marker) == 1
inc = inc.replace(marker, '    if(graphics_run_script("/graphics/apply-msdp-local-v1.sh")<0)return -1;\n'+marker)
(r/'tools/probe_graphics_v117.inc').write_text(inc, encoding='utf-8', newline='\n')
cmd = ('cd "/mnt/c/SHENG_WORKSPACE" && '
       'aarch64-linux-gnu-gcc -static -O2 -Wall -Wextra -Werror tools/hmos_probe_v117.c -o work/vendor-migration-v117/hmos-probe && '
       'aarch64-linux-gnu-strip work/vendor-migration-v117/hmos-probe && '
       'aarch64-linux-gnu-gcc -nostdlib -static -Os -fno-stack-protector -fno-builtin -Wall -Wextra -Werror '
       '-Wl,-e,_start,-z,noexecstack,--build-id=none tools/vendor_payload_entry_v117.c -o work/vendor-migration-v117/init && '
       'aarch64-linux-gnu-strip work/vendor-migration-v117/init')
subprocess.run(['wsl','-d','Ubuntu-22.04','--','bash','-lc',cmd],check=True)
oldinit = parse((r/'work/stock_init_boot/ramdisk.cpio').read_bytes())
oldvendor = parse((r/'work/stock_vendor_boot/fragment_0_.lz4.cpio').read_bytes())
base = parse((r/'work/v116_verify_probe/ramdisk.cpio').read_bytes())
base_vendor = parse((r/'work/audio-vendor-boot-v116/roundtrip.cpio').read_bytes())
assert len(oldvendor) == 372
assert all(base_vendor[k] == v for k,v in oldvendor.items())
assert sha((r/'output/vendor_boot_hmos_audio_v116.img').read_bytes()) == 'e997f7880c11df5fbbdb1b90661e2fa627dd1ec32dd61f8746df8fff3c95196d'
base_image=(r/'output/vendor_boot_hmos_audio_v116.img').read_bytes()
base_page=struct.unpack_from('<I',base_image,12)[0]
base_hs=struct.unpack_from('<I',base_image,2096)[0]
base_rs=(base_hs+base_page-1)//base_page*base_page
base_size=struct.unpack_from('<I',base_image,24)[0]
(d/'base-v116.lz4').write_bytes(base_image[base_rs:base_rs+base_size])
subprocess.run([exe,'decompress',str(d/'base-v116.lz4'),str(d/'base-v116.cpio')],check=True,capture_output=True)
assert parse((d/'base-v116.cpio').read_bytes())==base_vendor
assert sha(base['init'][1]) == sha((r/'work/hmos_probe_v116').read_bytes())
payload = {k:v for k,v in base.items() if k not in oldinit or k == 'init'}
payload['hmos-probe'] = regular((d/'hmos-probe').read_bytes())
del payload['init']
payload['graphics/apply-msdp-local-v1.sh'] = regular((r/'compat/sheng-framework/msdp-local-v1/apply-msdp-local-v1.sh').read_bytes())
assert payload['init.android.original'][1] == oldinit['init'][1]
aliases = ['busybox','drm-probe','graphics','stock-gpu-firmware','hmos-ipc.ko','hmos-init-debug.cfg','hmos-hdf-graphics.hcb','hmos-native-hilog','init.android.original']
assert all(k in payload and k not in oldvendor and k not in oldinit for k in aliases)
newvendor = dict(base_vendor)
assert not any(k.startswith(prefix) for k in newvendor)
newvendor[prefix[:-1]] = regular(b'',0o40755)
newvendor.update({prefix+k:v for k,v in payload.items()})
manifest = {k:dict(bytes=len(v[1]),mode=oct(v[0][1]),sha256=sha(v[1])) for k,v in payload.items()}
newvendor[prefix+'MANIFEST.json'] = regular((json.dumps(manifest,indent=2)+'\n').encode(),0o100644)
vendor_cpio = pack(newvendor); newvendor=parse(vendor_cpio); (d/'ramdisk.cpio').write_bytes(vendor_cpio)
subprocess.run([exe,'compress=lz4_legacy',str(d/'ramdisk.cpio'),str(d/'ramdisk.lz4')],check=True,capture_output=True)
compressed = (d/'ramdisk.lz4').read_bytes()
src = (stock/'vendor_boot.img').read_bytes()
version,page = struct.unpack_from('<II',src,8)
ram_size = struct.unpack_from('<I',src,24)[0]
hs,ds = struct.unpack_from('<II',src,2096)
ts,ne,es,bs = struct.unpack_from('<IIII',src,2112)
assert src[:8]==b'VNDRBOOT' and version==4 and hs==2128 and ne==1
align=lambda n:(n+page-1)//page*page
rs=align(hs); dt=rs+align(ram_size); tt=dt+align(ds); bc=tt+align(ts)
table=bytearray(src[tt:tt+ts]); assert struct.unpack_from('<II',table)==(ram_size,0)
struct.pack_into('<I',table,0,len(compressed))
image=bytearray(src[:rs]); struct.pack_into('<I',image,24,len(compressed))
for blob in [compressed,src[dt:dt+ds],table,src[bc:bc+bs]]:
    image.extend(blob); image.extend(bytes((-len(image))%page))
assert len(image)<len(src)-4096
image.extend(bytes(len(src)-len(image)))
vb=r/'output/vendor_boot_hmos_compat_v117.img'; vb.write_bytes(image)
# Generic ramdisk contains the stock scaffolding and this tiny entry only.
newinit=dict(oldinit); newinit['init']=(oldinit['init'][0],(d/'init').read_bytes())
newinit=parse(pack(newinit))
ibuild=d/'generic'; ibuild.mkdir(exist_ok=True)
(ibuild/'ramdisk.cpio').write_bytes(pack(newinit))
(ibuild/'header').write_bytes((r/'work/stock_init_boot/header').read_bytes())
ib=r/'output/init_boot_hmos_entry_v117.img'
subprocess.run([exe,'repack',str(stock/'init_boot.img'),str(ib)],cwd=ibuild,check=True,capture_output=True)
# Independent unpack/decompress, including every unchanged vendor entry and audio asset.
check=d/'verify';check.mkdir(exist_ok=True)
subprocess.run([exe,'unpack','-h',str(ib)],cwd=check,check=True,capture_output=True)
actual_init=parse((check/'ramdisk.cpio').read_bytes())
assert actual_init==newinit and set(actual_init)==set(oldinit)
assert len(actual_init['init'][1])<16384
subprocess.run([exe,'decompress',str(d/'ramdisk.lz4'),str(d/'roundtrip.cpio')],check=True,capture_output=True)
actual_vendor=parse((d/'roundtrip.cpio').read_bytes()); assert actual_vendor==newvendor
assert all(actual_vendor[k]==v for k,v in base_vendor.items())
ns=struct.unpack_from('<I',image,24)[0]; nd=rs+align(ns); nt=nd+align(ds); nb=nt+align(ts)
assert image[nd:nd+ds]==src[dt:dt+ds] and image[nb:nb+bs]==src[bc:bc+bs]
assert image[nt+4:nt+ts]==src[tt+4:tt+ts]
assert image[:24]==src[:24] and image[28:rs]==src[28:rs]
assert len(image)==100663296 and ib.stat().st_size==8388608
assert b'apply-msdp-local-v1.sh' in payload['hmos-probe'][1]
for blob in [payload['hmos-probe'][1],actual_init['init'][1],payload['busybox'][1]]:
    assert blob[:4]==b'\x7fELF' and struct.unpack_from('<H',blob,18)[0]==183
report=dict(version='v117',vendor_boot=dict(file=vb.name,bytes=len(image),sha256=sha(image)),
            init_boot=dict(file=ib.name,bytes=ib.stat().st_size,sha256=sha(ib.read_bytes())),
            original_vendor_entries=len(oldvendor),preserved_original_entries=True,preserved_v116_audio=True,
            dtb_unchanged=True,bootconfig_unchanged=True,ramdisk_table_unchanged_except_size=True,
            generic_entry_bytes=len(actual_init['init'][1]),generic_names=list(actual_init),
            payload_prefix=prefix,aliases=aliases,payload_entries=len(payload),compressed_ramdisk_bytes=len(compressed),
            cpio_verified=True,msdp_persistent=True,physical_cold_boot_verified=False)
(r/'analysis/vendor-migration-v117-verification.json').write_text(json.dumps(report,indent=2)+'\n')
(r/'output/v117-payload-manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
print(json.dumps(report,indent=2))
