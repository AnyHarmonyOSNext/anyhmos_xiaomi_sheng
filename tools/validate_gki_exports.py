"""Run in WSL: require unchanged old ABI and canonical CFI table pointers."""
from pathlib import Path
import json,struct
root=Path(__file__).resolve().parent.parent
base=Path('/root/hmos-work/gki-out-stock');new=Path('/root/hmos-work/gki-out-sheng-exports')
def symbols(path):
    return {p[1]:(int(p[0],16),tuple(p[3:])) for p in (x.split() for x in path.read_text().splitlines()) if len(p)>=4}
old,now=symbols(base/'vmlinux.symvers'),symbols(new/'vmlinux.symvers')
removed=sorted(old.keys()-now.keys());added=sorted(now.keys()-old.keys())
changed={n:[old[n],now[n]] for n in old.keys()&now.keys() if old[n]!=now[n]}
assert not removed and not changed,(removed,changed)
assert added==['sheng_hmos_ipc_api_v1'],added
before=(base/'.config').read_text().splitlines();after=(new/'.config').read_text().splitlines()
before=[x for x in before if not x.startswith('CONFIG_UNUSED_KSYMS_WHITELIST=')]
after=[x for x in after if not x.startswith('CONFIG_UNUSED_KSYMS_WHITELIST=')]
assert before==after,'Unexpected kernel config changes'
assert 'CONFIG_CFI_CLANG=y' in after and '# CONFIG_CFI_PERMISSIVE is not set' in after
sy={p[2]:int(p[0],16) for p in (x.split(maxsplit=2) for x in (new/'System.map').read_text().splitlines())}
b=(new/'vmlinux').read_bytes();off=struct.unpack_from('<Q',b,32)[0];sz,count=struct.unpack_from('<HH',b,54)
segments=[struct.unpack_from('<IIQQQQQQ',b,off+i*sz) for i in range(count)]
def filepos(v):return next(p[2]+v-p[3] for p in segments if p[0]==1 and p[3]<=v<p[3]+p[5])
table=filepos(sy['sheng_hmos_ipc_api_v1']);magic,version,size=struct.unpack_from('<QII',b,table)
names=json.loads((root/'analysis/gki-sheng-exports-preparation.json').read_text())['typed_private_apis']
assert (magic,version,size)==(0x5348454e47495043,1,16+8*len(names))
entries={}
for i,name in enumerate(names):
    ptr=struct.unpack_from('<Q',b,table+16+i*8)[0]
    assert sy['__cfi_jt_start']<=ptr<sy['__cfi_jt_end'],(name,hex(ptr))
    hint,branch=struct.unpack_from('<II',b,filepos(ptr));assert hint==0xd503245f and branch&0xfc000000==0x14000000,name
    imm=branch&0x3ffffff
    if imm&0x2000000:imm-=0x4000000
    target=ptr+4+imm*4
    assert target==sy[name],(name,hex(target),hex(sy[name]))
    entries[name]={'canonical':hex(ptr),'implementation':hex(target)}
report={'unchanged_old_exports':len(old),'removed':removed,'changed':changed,'added':added,
        'cfi_enabled':True,'cfi_permissive':False,'typed_canonical_entries':entries,
        'module_layout':f'0x{now["module_layout"][0]:08x}','config_matches_stock_except_whitelist_path':True}
(root/'analysis/gki-sheng-exports-verification.json').write_text(json.dumps(report,indent=2))
print(json.dumps({k:v for k,v in report.items() if k!='typed_canonical_entries'},indent=2));print('Canonical CFI pointers verified:',len(entries))
