from pathlib import Path
import struct,gzip,subprocess,json,hashlib
root=Path.cwd();work=root/'work/probe_build';work.mkdir(exist_ok=True);output=root/'output';output.mkdir(exist_ok=True)
stock=Path('E:/SHENG_STOCK_303/images');magisk='C:/MIO-KITCHEN-PYSIDE6-5.0.0-PREVIEW/bin/Windows/AMD64/magiskboot.exe'
subprocess.run(['wsl','-d','Ubuntu-22.04','--','bash','-lc','cd "/mnt/c/SHENG_WORKSPACE" && aarch64-linux-gnu-gcc -static -O2 -Wall -Wextra -Werror -o work/hmos_probe tools/hmos_probe.c && aarch64-linux-gnu-strip work/hmos_probe'],check=True)
subprocess.run(['wsl','-d','Ubuntu-22.04','--','bash','-lc','cd "/mnt/c/SHENG_WORKSPACE" && aarch64-linux-gnu-gcc -DTRACE_ANDROID -static -O2 -Wall -Wextra -Werror -o work/hmos_trace tools/hmos_probe.c && aarch64-linux-gnu-strip work/hmos_trace'],check=True)
# Edit the original newc archive without extracting to NTFS: preserve metadata.
b=(root/'work/stock_init_boot/ramdisk.cpio').read_bytes();i=0;rows=[]
while i+110<=len(b) and b[i:i+6] in [b'070701',b'070702']:
 vals=[int(b[i+6+j*8:i+14+j*8],16) for j in range(13)];name=b[i+110:i+110+vals[11]-1].decode();o=(i+110+vals[11]+3)&~3;data=b[o:o+vals[6]];i=(o+vals[6]+3)&~3
 if name=='TRAILER!!!':break
 if name=='init':
  rows.append(('init.android.original',vals.copy(),data));data=(root/'work/hmos_probe').read_bytes()
 rows.append((name,vals,data))
def pack(entries):
 out=bytearray()
 for name,vals,data in entries+[('TRAILER!!!',[0,0,0,0,1,0,0,0,0,0,0,0,0],b'')]:
  vals=vals.copy();vals[6]=len(data);nb=name.encode()+b'\0';vals[11]=len(nb);vals[12]=0
  out.extend(b'070701'+''.join(f'{x:08x}' for x in vals).encode()+nb);out.extend(bytes((-len(out))%4));out.extend(data);out.extend(bytes((-len(out))%4))
 out.extend(bytes((-len(out))%512));return bytes(out)
ramdisk=pack(rows);(work/'ramdisk.cpio').write_bytes(ramdisk)
(work/'header').write_bytes((root/'work/stock_init_boot/header').read_bytes())
subprocess.run([magisk,'repack',str(stock/'init_boot.img'),str(output/'init_boot_hmos_probe_v1.img')],cwd=work,check=True)
trace_rows=[(n,v,(root/'work/hmos_trace').read_bytes() if n=='init' else d) for n,v,d in rows]
(work/'ramdisk.cpio').write_bytes(pack(trace_rows))
subprocess.run([magisk,'repack',str(stock/'init_boot.img'),str(output/'init_boot_hmos_trace_v1.img')],cwd=work,check=True)
(work/'ramdisk.cpio').write_bytes(ramdisk)
# QEMU test archive needs only the static probe. No original OEM modules under virt.
vals=[1,0o100755,0,0,1,0,0,0,0,0,0,0,0];qemu=pack([('init',vals,(root/'work/hmos_probe').read_bytes())]);(work/'qemu_probe.cpio.gz').write_bytes(gzip.compress(qemu,mtime=0))
import shutil
shutil.copy2(stock/'init_boot.img',output/'init_boot_stock_303.img')
manifest={}
for p in [stock/'boot.img',stock/'init_boot.img',stock/'vendor_boot.img',output/'init_boot_hmos_probe_v1.img',output/'init_boot_hmos_trace_v1.img',output/'init_boot_stock_303.img',root/'work/hmos_probe',root/'work/hmos_trace',root/'tools/hmos_probe.c']:
 h=hashlib.file_digest(p.open('rb'),'sha256').hexdigest();manifest[str(p)]={'bytes':p.stat().st_size,'sha256':h}
(output/'manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2),encoding='utf-8')
print('image_bytes', (output/'init_boot_hmos_probe_v1.img').stat().st_size)
