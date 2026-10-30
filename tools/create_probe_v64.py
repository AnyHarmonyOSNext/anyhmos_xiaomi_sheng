"""Add the donor UI appearance service required by the real lockscreen clock."""
from pathlib import Path
import json
import shutil

r = Path(__file__).resolve().parent.parent
for n in ['hmos_probe.c', 'probe_graphics.inc', 'probe_command.inc']:
    p = r / 'tools' / n
    q = r / 'tools/archive' / (p.stem + '_v63' + p.suffix)
    if not q.exists():
        shutil.copy2(p, q)
d = r / 'compat/sheng-graphics/v64'
assert not d.exists()
shutil.copytree(r / 'compat/sheng-graphics/v63', d)
cfg = json.loads((d / 'init-desktop-services.cfg').read_text())
donor = json.loads((r / 'work/hmos_system/system/system/etc/init/ui_service.cfg').read_text())
svc = donor['services'][0]
svc.update({'once': 1, 'disabled': 1, 'saspawn': False, 'start-mode': 'condition'})
cfg['services'].append(svc)
cfg['jobs'].append({'name': 'param:sheng-debug-ui-appearance',
                    'condition': 'sheng.debug.start.ui=true', 'cmds': ['start ui_service']})
(d / 'init-desktop-services.cfg').write_text(json.dumps(cfg, indent=2) + '\n')
shutil.copy2(r / 'tools/configs/init-core-v63.cfg', r / 'tools/configs/init-core-v64.cfg')
p = r / 'tools/hmos_probe.c'
p.write_text(p.read_text().replace('v63', 'v64'))
for n in ['build_probe', 'verify']:
    source = (r / f'tools/{n}_v63.py').read_text().replace('v63', 'v64')
    if n == 'verify':
        source = source.replace("'theme_manager_service','wallpaper_service'}",
                                "'theme_manager_service','wallpaper_service','ui_service'}")
    (r / f'tools/{n}_v64.py').write_text(source)
print('v64: donor UI appearance SA7002; original identity and permissions; vendor untouched')
