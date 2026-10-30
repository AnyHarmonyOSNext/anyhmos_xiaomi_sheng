from pathlib import Path
import json,re
p=Path('work/stock_vendor_boot/fragment_0_.lz4.cpio'); b=p.read_bytes(); i=0;rows=[];out=Path('analysis/stock_vendor_text');out.mkdir(exist_ok=True)
while i+110<=len(b) and b[i:i+6] in [b'070701',b'070702']:
 v=[int(b[i+6+j*8:i+14+j*8],16) for j in range(13)];n=b[i+110:i+110+v[11]-1].decode(errors='replace');o=(i+110+v[11]+3)&~3;d=b[o:o+v[6]];rows.append(dict(name=n,mode=oct(v[1]),size=v[6]));i=(o+v[6]+3)&~3
 if ('fstab' in n or 'modules.load' in n or n.endswith('.rc') or 'modules.options' in n) and v[6]<500000:
  dest=out/n;dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes(d)
  if 'fstab' in n or 'modules.load' in n: print(n, d.decode(errors='replace')[:16000])
 if n=='TRAILER!!!':break
Path('analysis/stock_vendor_cpio.json').write_text(json.dumps(rows,indent=2));print('entries',len(rows));print('USB modules',[x['name'] for x in rows if any(y in x['name'] for y in ['usb','dwc3','gsi','acm','serial'])])
