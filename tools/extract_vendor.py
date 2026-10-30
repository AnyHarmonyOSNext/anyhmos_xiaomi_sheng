from pathlib import Path
import subprocess,re,gzip
root=Path.cwd();exe='C:/MIO-KITCHEN-PYSIDE6-5.0.0-PREVIEW/bin/Windows/AMD64/extract.erofs.exe'
for name in ['vendor','chip_prod']:
 image=f'C:/MIO-KITCHEN-PYSIDE6-5.0.0-PREVIEW/hmos/{name}.img'; dest=root/'work'/('hmos_'+name);dest.mkdir(exist_ok=True)
 for p in ['/etc','/build.prop']:
  r=subprocess.run([exe,'-i',image,'-X',p,'-o',str(dest),'-s'],capture_output=True);print(name,p,r.returncode)
b=(root/'work/stock_boot/kernel').read_bytes();pos=b.find(b'IKCFG_ST');end=b.find(b'IKCFG_ED',pos);print('ikconfig',pos,end)
if pos>=0:(root/'analysis/kernel.config').write_bytes(gzip.decompress(b[pos+8:end]))
