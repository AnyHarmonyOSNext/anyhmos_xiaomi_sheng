"""Start only the donor locator state SA2802, without GNSS/provider SAs."""
from pathlib import Path
import json
import shutil

r = Path(__file__).resolve().parent.parent
for n in ['hmos_probe.c', 'probe_graphics.inc', 'probe_command.inc']:
    p = r / 'tools' / n
    q = r / 'tools/archive' / (p.stem + '_v66' + p.suffix)
    if not q.exists():
        shutil.copy2(p, q)
d = r / 'compat/sheng-graphics/v67'
assert not d.exists()
shutil.copytree(r / 'compat/sheng-graphics/v66', d)
shutil.copy2(r / 'tools/configs/init-core-v66.cfg', r / 'tools/configs/init-core-v67.cfg')
cfg = json.loads((d / 'init-desktop-services.cfg').read_text())
svc = json.loads((r / 'work/hmos_system/system/system/etc/init/locationsa.cfg').read_text())['services'][0]
svc.pop('critical', None)
svc.pop('ondemand', None)
svc.update({'disabled': 1, 'once': 1, 'saspawn': False, 'start-mode': 'condition'})
cfg['services'].append(svc)
cfg['jobs'].append({'name': 'param:sheng-debug-location-state',
                    'condition': 'sheng.debug.start.location=true', 'cmds': [
                        'mkdir /data/service/el1/public/location 0711 gps gps',
                        'mkdir /data/service/el2/public/location 0711 gps gps',
                        'start locationhub']})
(d / 'init-desktop-services.cfg').write_text(json.dumps(cfg, indent=2) + '\n')
profile = json.loads((r / 'work/hmos_system/system/system/profile/locationhub.json').read_text())
profile['systemability'] = [x for x in profile['systemability'] if x['name'] == 2802]
assert len(profile['systemability']) == 1
profile['systemability'][0]['run-on-create'] = True
(d / 'locationhub-state.json').write_text(json.dumps(profile, indent=2) + '\n')
p = r / 'tools/probe_graphics.inc'
s = p.read_text()
mark = '    if(copy_ram_asset("/graphics/foundation-screen-only.json","/hmos-root/system/profile/foundation.json",0644)<0)return -1;'
assert s.count(mark) == 1
s = s.replace(mark, mark + '\n    if(copy_ram_asset("/graphics/locationhub-state.json","/hmos-root/system/profile/locationhub.json",0644)<0)return -1;')
p.write_text(s)
p = r / 'tools/hmos_probe.c'
p.write_text(p.read_text().replace('v66', 'v67'))
for n in ['build_probe', 'verify']:
    source = (r / f'tools/{n}_v66.py').read_text().replace('v66', 'v67')
    if n == 'verify':
        source = source.replace("'wallpaper_service','ui_service'}", "'wallpaper_service','ui_service','locationhub'}")
    (r / f'tools/{n}_v67.py').write_text(source)
print('v67: original location state SA2802 only; no GNSS/provider SA enabled')
