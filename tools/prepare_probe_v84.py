"""Isolate brightness on the fixed-mode display baseline; preserve v82/v83."""
from pathlib import Path
import json
import shutil

r = Path(__file__).resolve().parent.parent
d = r / 'compat/sheng-graphics/v84'
assert not d.exists(), 'v84 already staged'
shutil.copytree(r / 'compat/sheng-graphics/v83', d)
for p in list(d.iterdir()):
    if p.is_file() and (p.suffix in {'.sh', '.cfg'}):
        s = p.read_text(encoding='utf-8').replace('v83', 'v84').replace('V83', 'V84')
        dest = p.with_name(p.name.replace('v83', 'v84'))
        if dest != p:
            p.unlink()
        dest.write_text(s, encoding='utf-8', newline='\n')
for name in ['hmos_probe_v83.c', 'probe_graphics_v83.inc', 'probe_command_v83.inc',
             'build_probe_v83.py', 'verify_v83.py', 'start_native_desktop_v83.sh']:
    p = r / 'tools' / name
    s = p.read_text(encoding='utf-8').replace('v83', 'v84')
    if name == 'verify_v83.py':
        s = s.replace('hardware-display-v1/', 'brightness-v1/')
        s = s.replace("=={'powermgr','deviceinfoservice','media_service'}", "=={'powermgr'}")
        s = s.replace('displaymgr-profile.json', 'powermgr.json')
    p.with_name(name.replace('v83', 'v84')).write_text(s, encoding='utf-8', newline='\n')
p = r / 'tools/configs/init-core-v84.cfg'
p.write_text((r / 'tools/configs/init-core-v83.cfg').read_text(encoding='utf-8').replace('v83', 'v84'), encoding='utf-8', newline='\n')
shutil.copy2(r / 'compat/sheng-graphics/brightness-v1/libdisplay_composer_vdi_impl.z.so', d / 'libdisplay_composer_vdi_impl.z.so')
(d / 'displaymgr-profile.json').rename(d / 'powermgr.json')
p = d / 'init-hardware-v84.cfg'
c = json.loads(p.read_text(encoding='utf-8'))
c['jobs'][0]['cmds'] = ['start powermgr']
c['services'] = [s for s in c['services'] if s['name'] == 'powermgr']
c['services'][0]['path'] = ['/compat/bin/native_brightness_launcher']
p.write_text(json.dumps(c, indent=2) + '\n', encoding='utf-8', newline='\n')
p = d / 'apply-hardware-v84.sh'
s = p.read_text(encoding='utf-8').replace('displaymgr-profile.json', 'powermgr.json')
s = s.replace('sheng_hardware_display hardware_observe;', 'sheng_hardware_display hardware_observe native_brightness_launcher;')
s += '\n: > $R/data/local/tmp/sheng-brightness-stderr.txt\n$B chown 5528:5528 $R/data/local/tmp/sheng-brightness-stderr.txt\n$B chmod 0600 $R/data/local/tmp/sheng-brightness-stderr.txt\n'
p.write_text(s, encoding='utf-8', newline='\n')
shutil.copy2(r / 'compat/debug-tools/native_brightness_launcher', d / 'native_brightness_launcher')
print('v84 staged: fixed preferred mode, native brightness only; build/verify required')
