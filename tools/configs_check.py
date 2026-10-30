from pathlib import Path
import re,gzip
p=Path('work/stock_boot/kernel'); b=p.read_bytes()
for m in re.finditer(b'IKCFG_ST',b):
 pos=m.start();end=b.find(b'IKCFG_ED',pos)
 print(pos,end)
 try:
  c=gzip.decompress(b[pos+8:end]);print(c[:200]);Path(f'analysis/kernel-config-{pos}.txt').write_bytes(c)
 except Exception as e:print(e)
for p in Path('work').glob('stock_*/*'):
 if p.is_file() and p.name=='kernel': print(p,p.stat().st_size,b[:80].hex())
