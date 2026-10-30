import pathlib,struct
roots=[pathlib.Path('C:/MIO-KITCHEN-PYSIDE6-5.0.0-PREVIEW/hmos'),pathlib.Path('C:/Users/YOUR_USER/Downloads/FastbootFlasher_Ver1.8_x64/images')]
for root in roots:
 for p in root.glob('*.img'):
  with p.open('rb') as f:
   b=f.read(4096)
  print(str(p),p.stat().st_size, b[:32].hex(), 'ext4',b[1080:1082].hex(),'erofs',b[1024:1028].hex())
  if b[:4]==bytes.fromhex('3aff26ed'): print('sparse',struct.unpack_from('<I4H4I',b))
