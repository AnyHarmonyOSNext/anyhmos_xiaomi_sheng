"""Return unavailable before the donor WiFi SDK's hidden blocking proxy query."""
from pathlib import Path
import shutil,struct,hashlib,json
r=Path(__file__).resolve().parent.parent
for n in ['hmos_probe.c','probe_graphics.inc','probe_command.inc']:
 p=r/'tools'/n;q=r/'tools/archive'/(p.stem+'_v60'+p.suffix)
 if not q.exists():shutil.copy2(p,q)
d=r/'compat/sheng-graphics/v61';assert not d.exists()
shutil.copytree(r/'compat/sheng-graphics/v60',d)
cfg=json.loads((r/'tools/configs/init-core-v60.cfg').read_text())
next(x for x in cfg['services'] if x['name']=='appspawn').pop('env',None)
(r/'tools/configs/init-core-v61.cfg').write_text(json.dumps(cfg,indent=2)+'\n')
src=r/'work/hmos_system/system/system/lib64/platformsdk/libwifi_sdk.z.so'
b=src.read_bytes();assert hashlib.sha256(b).hexdigest()=='06765b1a54ac5c861baf5902f9081bb7da93a3b6765ae53085e150d3d7a00368'
va=0x4e628;phoff=struct.unpack_from('<Q',b,32)[0];phsize,phnum=struct.unpack_from('<HH',b,54)
offset=None
for i in range(phnum):
 kind,flags,off,addr,paddr,filesz,memsz,align=struct.unpack_from('<IIQQQQQQ',b,phoff+i*phsize)
 if kind==1 and addr<=va and va+8<=addr+filesz:offset=off+va-addr
assert offset is not None
old=bytes.fromhex('ef0100d0ef1141f9');assert b[offset:offset+8]==old
# Callers at 0x49c84/0x4e544 branch to their error path when bit0 is zero.
# Function returns bool and keeps its proxy in this+56; no hidden sret ABI.
out=bytearray(b);out[offset:offset+8]=bytes.fromhex('00008052c0035fd6') # mov w0,0; ret
(d/'libwifi_sdk.z.so').write_bytes(out)
report={'scope':'development WiFi device SDK unavailable, no successful state or network operation','function_va':hex(va),'file_offset':offset,'original':old.hex(),'replacement':out[offset:offset+8].hex(),'input_sha256':hashlib.sha256(b).hexdigest(),'output_sha256':hashlib.sha256(out).hexdigest(),'donor_build_id':'094b827ea2cba31bd0c212a982b2e4c9','caller_error_branch_va':['0x49c88','0x4e548'],'vendor_modified':False}
(r/'analysis/v61-wifi-unavailable-patch.json').write_text(json.dumps(report,indent=2)+'\n')
p=r/'tools/probe_graphics.inc';s=p.read_text()
mark='    if(copy_ram_asset("/graphics/libsheng_wifi_ui_unavailable.so","/hmos-root/compat/lib64/libsheng_wifi_ui_unavailable.so",0644)<0)return -1;'
assert s.count(mark)==1
s=s.replace(mark,'    if(copy_ram_asset("/graphics/libwifi_sdk.z.so","/hmos-root/compat/lib64/libwifi_sdk.z.so",0644)<0)return -1;');p.write_text(s)
p=r/'tools/hmos_probe.c';p.write_text(p.read_text().replace('v60','v61'))
for n in ['build_probe','verify']:
 (r/f'tools/{n}_v61.py').write_text((r/f'tools/{n}_v60.py').read_text().replace('v60','v61'))
print(json.dumps(report,indent=2))
