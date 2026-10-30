from pathlib import Path
import hashlib, json, struct, sys
root=Path(__file__).resolve().parent.parent
p=root/(sys.argv[1] if len(sys.argv)>1 else 'compat/sheng-hmos-ipc/sheng_hmos_ipc.ko')
b=p.read_bytes();shoff=struct.unpack_from('<Q',b,40)[0];size,count,index=struct.unpack_from('<HHH',b,58)
sections=[struct.unpack_from('<IIQQQQIIQQ',b,shoff+i*size) for i in range(count)]
s=sections[index];names=b[s[4]:s[4]+s[5]];imports={};info=b''
for s in sections:
 name=names[s[0]:].split(b'\0',1)[0];data=b[s[4]:s[4]+s[5]]
 if name==b'__versions':
  assert len(data)%64==0
  for i in range(0,len(data),64):imports[data[i+8:i+64].split(b'\0',1)[0].decode()]=struct.unpack_from('<Q',data,i)[0]
 if name==b'.modinfo':info=data
 assert name not in (b'.BTF',b'.BTF.ext')
built={line.split()[1]:int(line.split()[0],16) for line in Path('/root/hmos-work/gki-out-stock/vmlinux.symvers').read_text().splitlines() if line.strip()}
assert imports and all(built.get(name)==crc for name,crc in imports.items())
stock=json.loads((root/'analysis/stock-module-import-crcs.json').read_text())['symbols']
observed=sorted(imports.keys()&stock.keys())
assert all(imports[name]==int(stock[name],16) for name in observed)
assert b'vermagic=5.15.178-android13-8-00021-g6f2f96be86b9-ab13729987 ' in info
assert b'__cfi_check\0' in b and imports['module_layout']==0x0222dd63
report={'sha256':hashlib.sha256(b).hexdigest(),'bytes':len(b),'imports_checked_against_rebuilt_gki':len(imports),'also_observed_in_stock_modules':len(observed),'cfi_check_present':True,'module_btf_removed':True,'runtime_tested':False}
report['artifact']=str(p.relative_to(root))
name='sheng-ipc-'+p.parent.name+'-abi-verification.json' if p.parent.name.startswith('v') else 'sheng-ipc-abi-verification.json'
(root/'analysis'/name).write_text(json.dumps(report,indent=2));print(json.dumps(report,indent=2))
