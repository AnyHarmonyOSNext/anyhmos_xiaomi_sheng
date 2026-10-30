from pathlib import Path
import subprocess,struct,json,sys,hashlib
version='v13';root=Path.cwd();exe='C:/MIO-KITCHEN-PYSIDE6-5.0.0-PREVIEW/bin/Windows/AMD64/magiskboot.exe'
def parse(b):
 i=0;out={}
 while i+110<=len(b) and b[i:i+6]==b'070701':
  v=[int(b[i+6+j*8:i+14+j*8],16) for j in range(13)];n=b[i+110:i+110+v[11]-1].decode();o=(i+110+v[11]+3)&~3;out[n]=(v,b[o:o+v[6]]);i=(o+v[6]+3)&~3
  if n=='TRAILER!!!':return out
 raise ValueError('No CPIO trailer')
old=parse((root/'work/stock_init_boot/ramdisk.cpio').read_bytes());results={}
for mode in ['probe','trace']:
 image=root/f'output/init_boot_hmos_{mode}_{version}.img';dest=root/f'work/{version}_verify_{mode}';dest.mkdir(exist_ok=True)
 subprocess.run([exe,'unpack','-h',str(image)],cwd=dest,check=True,capture_output=True)
 new=parse((dest/'ramdisk.cpio').read_bytes());binary=(root/f'work/hmos_{mode}_{version}').read_bytes();assert new['init'][1]==binary;assert new['init.android.original'][1]==old['init'][1];assert new['init.android.original'][0][:11]==old['init'][0][:11]
 for k,v in old.items():
  if k not in ['init','TRAILER!!!']:assert new[k]==v,k
 assert image.stat().st_size==8388608
 assert new['hmos-init-debug.cfg'][1]==(root/'tools/configs/init-core-v13.cfg').read_bytes()
 config=json.loads(new['hmos-init-debug.cfg'][1]);assert len(config['services'])==1 and config['services'][0]['once']==1 and 'critical' not in config['services'][0]
 assert binary[:4]==b'\x7fELF' and struct.unpack_from('<H',binary,18)[0]==183
 results[mode]={'bytes':image.stat().st_size,'sha256':hashlib.sha256(image.read_bytes()).hexdigest(),'cpio_verified':True,'original_init_preserved':True}
(root/f'analysis/{version}-image-verification.json').write_text(json.dumps(results,indent=2));print(json.dumps(results,indent=2))





