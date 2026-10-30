"""Preload the compatibility WiFi SDK before app namespaces choose donor SDK."""
from pathlib import Path
import shutil,json
r=Path(__file__).resolve().parent.parent
for n in ['hmos_probe.c','probe_graphics.inc','probe_command.inc']:
 p=r/'tools'/n;q=r/'tools/archive'/(p.stem+'_v61'+p.suffix)
 if not q.exists():shutil.copy2(p,q)
d=r/'compat/sheng-graphics/v62';assert not d.exists()
shutil.copytree(r/'compat/sheng-graphics/v61',d)
cfg=json.loads((r/'tools/configs/init-core-v61.cfg').read_text())
next(x for x in cfg['services'] if x['name']=='appspawn')['env']=[{'name':'LD_PRELOAD','value':'/compat/lib64/libwifi_sdk.z.so'}]
(r/'tools/configs/init-core-v62.cfg').write_text(json.dumps(cfg,indent=2)+'\n')
p=r/'tools/hmos_probe.c';p.write_text(p.read_text().replace('v61','v62'))
for n in ['build_probe','verify']:
 (r/f'tools/{n}_v62.py').write_text((r/f'tools/{n}_v61.py').read_text().replace('v61','v62'))
print('v62: compatibility SDK preloaded into appspawn; no vendor overlays')
