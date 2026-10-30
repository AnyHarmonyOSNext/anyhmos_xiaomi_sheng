"""Include original on-demand WiFi state service so UI queries can complete."""
from pathlib import Path
import shutil,json
r=Path(__file__).resolve().parent.parent
for n in ['hmos_probe.c','probe_graphics.inc','probe_command.inc']:
 p=r/'tools'/n; q=r/'tools/archive'/(p.stem+'_v57'+p.suffix)
 if not q.exists():shutil.copy2(p,q)
d=r/'compat/sheng-graphics/v58';assert not d.exists()
shutil.copytree(r/'compat/sheng-graphics/v57',d)
cfg=json.loads((d/'init-desktop-services.cfg').read_text())
wifi=json.loads((r/'work/hmos_system/system/system/etc/init/wifi_standard.cfg').read_text())
svc=wifi['services'][0]
svc.update({'once':1,'saspawn':False,'disabled':1})
cfg['services'].append(svc)
job=next(x for x in wifi['jobs'] if x['name']=='services:wifi_manager_service')
job['cmds']=[
 'mkdir /data/update 0771 root root',
 'mkdir /data/service/el1/public/wifi 0770 wifi wifi',
 'mkdir /data/service/el2/public/wifi 0770 wifi wifi',
]+job['cmds']
cfg['jobs'].append(job)
cfg['jobs'].append({'name':'param:sheng-debug-wifi-state','condition':'sheng.debug.start.wifi=true','cmds':['start wifi_manager_service']})
(d/'init-desktop-services.cfg').write_text(json.dumps(cfg,indent=2)+'\n')
shutil.copy2(r/'tools/configs/init-core-v57.cfg',r/'tools/configs/init-core-v58.cfg')
for n in ['hmos_probe.c','probe_graphics.inc']:
 p=r/'tools'/n;s=p.read_text();p.write_text(s.replace('v57','v58'))
for n in ['build_probe','verify']:
 (r/f'tools/{n}_v58.py').write_text((r/f'tools/{n}_v57.py').read_text().replace('v57','v58'))
print('v58: original WiFi on-demand service; no HAL/kernel/vendor changes')
