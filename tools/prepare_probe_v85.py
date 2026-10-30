"""Start the real media dependency before SceneBoard and fix hardware triggers."""
from pathlib import Path
import json
import shutil

r = Path(__file__).resolve().parent.parent
d = r / 'compat/sheng-graphics/v85'
assert not d.exists(), 'v85 already staged'
shutil.copytree(r / 'compat/sheng-graphics/v84', d)
for p in list(d.iterdir()):
    if p.is_file() and p.suffix in {'.sh', '.cfg'}:
        s = p.read_text(encoding='utf-8').replace('v84', 'v85').replace('V84', 'V85')
        dest = p.with_name(p.name.replace('v84', 'v85'))
        if dest != p:
            p.unlink()
        dest.write_text(s, encoding='utf-8', newline='\n')
for name in ['hmos_probe_v84.c', 'probe_graphics_v84.inc', 'probe_command_v84.inc',
             'build_probe_v84.py', 'verify_v84.py']:
    p = r / 'tools' / name
    s = p.read_text(encoding='utf-8').replace('v84', 'v85')
    if name == 'verify_v84.py':
        s = s.replace("=={'powermgr'}", "=={'powermgr','media_service','av_session'}")
    p.with_name(name.replace('v84', 'v85')).write_text(s, encoding='utf-8', newline='\n')
p = r / 'tools/configs/init-core-v85.cfg'
p.write_text((r / 'tools/configs/init-core-v84.cfg').read_text(encoding='utf-8').replace('v84', 'v85'), encoding='utf-8', newline='\n')
p = d / 'init-hardware-v85.cfg'
c = json.loads(p.read_text(encoding='utf-8'))
c['jobs'][0]['name'] = 'param:sheng-hardware'
c['jobs'].append({'name': 'param:sheng-media', 'condition': 'sheng.debug.start.media=true',
                  'cmds': ['start media_service', 'start av_session']})
stock = r / 'work/hmos_system/system/system'
for filename in ['media_service.cfg', 'avsession_service.cfg']:
    original = json.loads((stock / 'etc/init' / filename).read_text(encoding='utf-8'))
    svc = original['services'][0]
    for key in ['critical', 'jobs', 'ondemand', 'writepid', 'bootevents']:
        svc.pop(key, None)
    svc.update(disabled=1, once=1, sandbox=0, saspawn=False)
    svc['start-mode'] = 'condition'
    c['services'].append(svc)
    c['jobs'].extend(original.get('jobs', []))
p.write_text(json.dumps(c, indent=2) + '\n', encoding='utf-8', newline='\n')
shutil.copy2(r / 'compat/debug-tools/native_sa_check', d / 'native_sa_check')
p = d / 'apply-hardware-v85.sh'
s = p.read_text(encoding='utf-8').replace('hardware_observe native_brightness_launcher;', 'hardware_observe native_brightness_launcher native_sa_check;')
p.write_text(s, encoding='utf-8', newline='\n')
p = d / 'start-native-desktop-v85.sh'
s = p.read_text(encoding='utf-8')
s = s.replace('stage=hardware\n$B chroot "$R" /system/bin/param set sheng.debug.start.hardware true\n', '')
needle = 'stage=graphics\n'
assert s.count(needle) == 1
s = s.replace(needle, '''stage=media
$B chroot "$R" /system/bin/param set sheng.debug.start.media true
deadline=$(($(now)+40))
while ! $B timeout 3 $B chroot "$R" /compat/bin/native_sa_check 3002; do
 [ "$(now)" -lt "$deadline" ] || exit 35
 $B sleep 1
done
echo AUTOSTART_ORIGINAL_MEDIA_SA3002_READY
stage=graphics
''')
needle = 'stage=touch\n'
assert s.count(needle) == 1
s = s.replace(needle, '''stage=hardware
$B chroot "$R" /system/bin/param set sheng.debug.start.hardware true
stage=touch
''')
p.write_text(s, encoding='utf-8', newline='\n')
shutil.copy2(p, r / 'tools/start_native_desktop_v85.sh')
print('v85 staged; media service readiness precedes SceneBoard, no fake media results')
