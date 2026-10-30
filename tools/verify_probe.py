from pathlib import Path
import hashlib,struct,json

def parse(b):
 i=0;out={}
 while i+110<=len(b) and b[i:i+6]==b'070701':
  v=[int(b[i+6+j*8:i+14+j*8],16) for j in range(13)];n=b[i+110:i+110+v[11]-1].decode();o=(i+110+v[11]+3)&~3;out[n]=(v,b[o:o+v[6]]);i=(o+v[6]+3)&~3
  if n=='TRAILER!!!':break
 return out
old=parse(Path('work/stock_init_boot/ramdisk.cpio').read_bytes());new=parse(Path('work/probe_verify/ramdisk.cpio').read_bytes())
assert new['init'][1]==Path('work/hmos_probe').read_bytes()
assert new['init.android.original'][1]==old['init'][1]
for k,v in old.items():
 if k not in ['init','TRAILER!!!']:assert v==new[k],k
img=Path('output/init_boot_hmos_probe_v1.img').read_bytes();oldimg=Path('output/init_boot_stock_303.img').read_bytes();assert len(img)==len(oldimg)==8388608
assert img[:8]==b'ANDROID!' and struct.unpack_from('<I',img,40)[0]==4
elf=new['init'][1];assert elf[:4]==b'\x7fELF' and struct.unpack_from('<H',elf,18)[0]==183
phoff=struct.unpack_from('<Q',elf,32)[0];phents,phnum=struct.unpack_from('<HH',elf,54);assert all(struct.unpack_from('<I',elf,phoff+i*phents)[0]!=3 for i in range(phnum))
r={'image_size':len(img),'header_version':4,'architecture':'AArch64','static_no_PT_INTERP':True,'stock_init_preserved':True,'other_cpio_entries_preserved':True,'sha256':hashlib.sha256(img).hexdigest()};Path('analysis/probe_verification.json').write_text(json.dumps(r,indent=2));print(r)
