"""Read reconstructed stock GKI branch targets; no device or source writes."""
from pathlib import Path
import re,struct,json
root=Path(__file__).resolve().parent.parent
gki=Path('/root/hmos-work/gki-out-stock')
symbols={}
for line in (gki/'System.map').read_text().splitlines():
    a,t,n=line.split(maxsplit=2);symbols[n]=int(a,16)
raw=(gki/'vmlinux').read_bytes()
offset=struct.unpack_from('<Q',raw,32)[0];size,count=struct.unpack_from('<HH',raw,54)
segments=[struct.unpack_from('<IIQQQQQQ',raw,offset+i*size) for i in range(count)]
def position(address):
    for p in segments:
        if p[0]==1 and p[3]<=address<p[3]+p[5]:return p[2]+address-p[3]
    raise ValueError(hex(address))
begin,end=symbols['__cfi_jt_start'],symbols['__cfi_jt_end']
targets={}
for address in range(begin,end,4):
    word=struct.unpack_from('<I',raw,position(address))[0]
    if word&0xfc000000!=0x14000000:continue
    imm=word&0x3ffffff
    if imm&0x2000000:imm-=0x4000000
    targets.setdefault(address+imm*4,[]).append(address)
names=re.findall(r'resolve_api\("([^"]+)"', (root/'compat/sheng-hmos-ipc/src/private_api.c').read_text())
report={name:{'implementation':hex(symbols[name]),'canonical_entries':[hex(x) for x in targets.get(symbols[name],[])]} for name in names}
(root/'analysis/stock-private-api-cfi-entries.json').write_text(json.dumps(report,indent=2))
for name,item in report.items():print(name,item)
