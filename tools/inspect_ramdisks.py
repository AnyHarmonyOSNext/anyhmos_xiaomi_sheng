from pathlib import Path
import struct,json
for folder in ['stock_init_boot','stock_vendor_boot']:
 p=Path('work')/folder/'ramdisk.cpio'; b=p.read_bytes(); print(folder,b[:16],len(b))
 if b[:6] in [b'070701',b'070702']:
  i=0; rows=[]
  while i+110<=len(b) and b[i:i+6] in [b'070701',b'070702']:
   v=[int(b[i+6+j*8:i+14+j*8],16) for j in range(13)]; n=b[i+110:i+110+v[11]-1].decode(errors='replace'); o=(i+110+v[11]+3)&~3; d=b[o:o+v[6]]
   rows.append({'name':n,'mode':oct(v[1]),'size':v[6]})
   if 'fstab' in n or n.endswith('.rc') or n in ['init','system/etc/ramdisk/build.prop']:
    if v[6]<100000: print(n, d.decode(errors='replace')[:25000])
   i=(o+v[6]+3)&~3
   if n=='TRAILER!!!': break
  Path('analysis',folder+'_cpio.json').write_text(json.dumps(rows,indent=2));print('entries',len(rows),'next',i,b[i:i+24].hex())
p=Path('C:/Users/YOUR_USER/Downloads/FastbootFlasher_Ver1.8_x64/images/boot.img'); b=p.read_bytes()
for tag in [b'ANDROID!',b'VNDRBOOT',b'070701',b'\x1f\x8b\x08']:
 print('huawei',tag,b.find(tag))
