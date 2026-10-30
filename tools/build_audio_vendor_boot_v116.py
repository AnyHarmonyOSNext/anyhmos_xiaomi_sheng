"""Add an isolated audio payload while preserving every original vendor entry."""
from pathlib import Path
import hashlib,json,struct,subprocess
r=Path(__file__).resolve().parent.parent
stock=Path('E:/SHENG_STOCK_303/images/vendor_boot.img')
exe='C:/MIO-KITCHEN-PYSIDE6-5.0.0-PREVIEW/bin/Windows/AMD64/magiskboot.exe'
d=r/'work/audio-vendor-boot-v116';d.mkdir(exist_ok=True)
src=stock.read_bytes()
assert src[:8]==b'VNDRBOOT'
version,page=struct.unpack_from('<II',src,8)
assert version==4
ram_size=struct.unpack_from('<I',src,24)[0]
header_size,dtb_size=struct.unpack_from('<II',src,2096)
table_size,num_entries,entry_size,bc_size=struct.unpack_from('<IIII',src,2112)
assert header_size==2128 and num_entries==1 and entry_size>=108
align=lambda n:(n+page-1)//page*page
ram_start=align(header_size);dtb_start=ram_start+align(ram_size)
table_start=dtb_start+align(dtb_size);bc_start=table_start+align(table_size)
table=bytearray(src[table_start:table_start+table_size])
entry_ram_size,entry_offset=struct.unpack_from('<II',table)
assert (entry_ram_size,entry_offset)==(ram_size,0)
old=(r/'work/stock_vendor_boot/fragment_0_.lz4.cpio').read_bytes()
def entries(b):
    pos=0; result={}
    while b[pos:pos+6]==b'070701':
        fields=[int(b[pos+6+i*8:pos+14+i*8],16) for i in range(13)]
        name=b[pos+110:pos+110+fields[11]-1].decode()
        start=(pos+110+fields[11]+3)&~3
        if name=='TRAILER!!!': return result,pos
        assert name not in result,name
        result[name]=(fields,b[start:start+fields[6]])
        pos=(start+fields[6]+3)&~3
    raise ValueError('Invalid original cpio')
old_entries,trailer=entries(old)
out=bytearray(old[:trailer])
def append(name,data,mode):
    assert name not in old_entries
    nb=name.encode()+b'\0';fields=[0,mode,0,0,1,0,len(data),0,0,0,0,len(nb),0]
    out.extend(b'070701'+''.join(f'{x:08x}' for x in fields).encode()+nb)
    out.extend(bytes((-len(out))%4));out.extend(data);out.extend(bytes((-len(out))%4))
append('sheng-audio-v1',b'',0o40755)
payload=r/'work/audio-persistent-v1'
for p in sorted(payload.rglob('*')):
    name='sheng-audio-v1/'+p.relative_to(payload).as_posix()
    if p.is_dir(): append(name,b'',0o40755)
    else:
        executable='/bin/' in name or name.endswith('.sh')
        append(name,p.read_bytes(),0o100755 if executable else 0o100644)
append('TRAILER!!!',b'',0)
out.extend(bytes((-len(out))%512))
cpio=d/'ramdisk.cpio';cpio.write_bytes(out)
new_entries,_=entries(out)
assert all(new_entries[k]==v for k,v in old_entries.items())
packed=d/'ramdisk.lz4'
subprocess.run([exe,'compress=lz4_legacy',str(cpio),str(packed)],check=True,capture_output=True)
compressed=packed.read_bytes();assert compressed[:4]==src[ram_start:ram_start+4]==bytes.fromhex('02214c18')
check=d/'roundtrip.cpio'
subprocess.run([exe,'decompress',str(packed),str(check)],check=True,capture_output=True)
assert check.read_bytes()==out
head=bytearray(src[:ram_start]);struct.pack_into('<I',head,24,len(compressed))
struct.pack_into('<I',table,0,len(compressed))
image=bytearray(head)
for blob in [compressed,src[dtb_start:dtb_start+dtb_size],table,src[bc_start:bc_start+bc_size]]:
    image.extend(blob);image.extend(bytes((-len(image))%page))
assert len(image)<len(src)-4096
image.extend(bytes(len(src)-len(image)))
target=r/'output/vendor_boot_hmos_audio_v116.img';target.write_bytes(image)
# Validate the constructed container independently using its new offsets.
ns=struct.unpack_from('<I',image,24)[0];nd=ram_start+align(ns);nt=nd+align(dtb_size);nb=nt+align(table_size)
assert image[nd:nd+dtb_size]==src[dtb_start:dtb_start+dtb_size]
assert image[nb:nb+bc_size]==src[bc_start:bc_start+bc_size]
assert image[nt+4:nt+table_size]==src[table_start+4:table_start+table_size]
assert image[:24]==src[:24] and image[28:ram_start]==src[28:ram_start]
report=dict(image=str(target.relative_to(r)),bytes=len(image),sha256=hashlib.sha256(image).hexdigest(),
    original_sha256=hashlib.sha256(src).hexdigest(),header_version=version,page_size=page,
    original_cpio_entries=len(old_entries),preserved_original_entries=True,added_prefix='sheng-audio-v1/',
    compressed_ramdisk_bytes=len(compressed),original_compressed_bytes=ram_size,
    dtb_unchanged=True,bootconfig_unchanged=True,ramdisk_table_unchanged_except_size=True,
    avb_footer='not copied: device AVB verification already disabled; no vbmeta writes')
(r/'analysis/vendor-boot-audio-v116-verification.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps(report,indent=2))
