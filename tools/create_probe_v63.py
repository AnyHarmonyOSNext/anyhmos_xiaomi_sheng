"""Bind only the compatibility system SDK at the app namespace's donor path."""
from pathlib import Path
import shutil,json
r=Path(__file__).resolve().parent.parent
for n in ['hmos_probe.c','probe_graphics.inc','probe_command.inc']:
 p=r/'tools'/n;q=r/'tools/archive'/(p.stem+'_v62'+p.suffix)
 if not q.exists():shutil.copy2(p,q)
d=r/'compat/sheng-graphics/v63';assert not d.exists()
shutil.copytree(r/'compat/sheng-graphics/v62',d)
cfg=json.loads((r/'tools/configs/init-core-v62.cfg').read_text())
next(x for x in cfg['services'] if x['name']=='appspawn').pop('env',None)
(r/'tools/configs/init-core-v63.cfg').write_text(json.dumps(cfg,indent=2)+'\n')
p=r/'tools/probe_graphics.inc';s=p.read_text()
mark='    if(copy_ram_asset("/graphics/libwifi_sdk.z.so","/hmos-root/compat/lib64/libwifi_sdk.z.so",0644)<0)return -1;'
assert s.count(mark)==1
s=s.replace(mark,mark+'\n    if(mount("/hmos-root/compat/lib64/libwifi_sdk.z.so","/hmos-root/system/lib64/platformsdk/libwifi_sdk.z.so",NULL,MS_BIND,NULL)<0)return -1;\n    note("SYSTEM_WIFI_SDK_COMPAT_BIND: absent device proxy returns false; vendor untouched");')
p.write_text(s)
p=r/'tools/hmos_probe.c';p.write_text(p.read_text().replace('v62','v63'))
for n in ['build_probe','verify']:
 (r/f'tools/{n}_v63.py').write_text((r/f'tools/{n}_v62.py').read_text().replace('v62','v63'))
print('v63: no appspawn preload; bind compat SDK only onto system RAM view')
