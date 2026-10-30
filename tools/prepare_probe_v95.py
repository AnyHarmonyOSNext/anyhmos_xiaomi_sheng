"""Expose mounted preload policy to BMS and start the original power service."""
from pathlib import Path
import shutil

r = Path(__file__).resolve().parent.parent
d = r / 'compat/sheng-graphics/v95'
assert not d.exists()
shutil.copytree(r / 'compat/sheng-graphics/v94', d)
for p in list(d.iterdir()):
    if p.is_file() and p.suffix in {'.sh', '.cfg'}:
        q = p.with_name(p.name.replace('v94', 'v95'))
        s = p.read_text(encoding='utf-8').replace('v94', 'v95').replace('V94', 'V95')
        if q != p:
            p.unlink()
        q.write_text(s, encoding='utf-8', newline='\n')
for name in ['hmos_probe_v94.c', 'probe_graphics_v94.inc', 'probe_command_v94.inc',
             'build_probe_v94.py', 'verify_v94.py', 'start_native_desktop_v94.sh']:
    s = (r / 'tools' / name).read_text(encoding='utf-8').replace('v94', 'v95')
    (r / 'tools' / name.replace('v94', 'v95')).write_text(s, encoding='utf-8', newline='\n')
(r / 'tools/configs/init-core-v95.cfg').write_text(
    (r / 'tools/configs/init-core-v94.cfg').read_text(encoding='utf-8').replace('v94', 'v95'),
    encoding='utf-8', newline='\n')
shutil.copyfile(r / 'tools/apply-preload.sh', d / 'apply-preload.sh')
shutil.copyfile(r / 'compat/sheng-power/service-v1/powermgr.json', d / 'powermgr.json')
p = r / 'tools/probe_graphics_v95.inc'
s = p.read_text(encoding='utf-8').replace(
    'if(graphics_run_script("/graphics/apply-runtime-v95.sh")<0)return -1;',
    'if(graphics_run_script("/graphics/apply-runtime-v95.sh")<0)return -1;\n'
    '    if(graphics_run_script("/graphics/apply-preload.sh")<0)return -1;')
assert s != p.read_text(encoding='utf-8')
p.write_text(s, encoding='utf-8', newline='\n')
for p in [r / 'tools/start_native_desktop_v95.sh', d / 'start-native-desktop-v95.sh']:
    s = p.read_text(encoding='utf-8').replace(
        'stage=complete\necho AUTOSTART_SERVICES_READY=1',
        '# SceneBoard, account, unlock and native capture have actually completed.\n'
        '$B chroot "$R" /system/bin/param set bootevent.boot.completed true\n'
        'echo AUTOSTART_REAL_BOOT_COMPLETED_EVENT=1\n'
        'stage=complete\necho AUTOSTART_SERVICES_READY=1')
    assert 'AUTOSTART_REAL_BOOT_COMPLETED_EVENT=1' in s
    p.write_text(s, encoding='utf-8', newline='\n')
p = r / 'tools/verify_v95.py'
s = p.read_text(encoding='utf-8').replace(
    "['systemability']]==[3308]", "['systemability']]==[3308,3301]")
s = s.replace("assert b'AUTOSTART_SERVICES_READY=1' in new['graphics/start-native-desktop-v95.sh'][1]", """assert b'AUTOSTART_SERVICES_READY=1' in new['graphics/start-native-desktop-v95.sh'][1]
 assert b'AUTOSTART_REAL_BOOT_COMPLETED_EVENT=1' in new['graphics/start-native-desktop-v95.sh'][1]
 assert b'apply-preload.sh' in binary
 assert b'/preload/WKI-W10/all/cn' in new['graphics/apply-preload.sh'][1]
 assert new['graphics/powermgr.json'][1]==(root/'compat/sheng-power/service-v1/powermgr.json').read_bytes()""")
p.write_text(s, encoding='utf-8', newline='\n')
print('v95 staged: native preload scan path and power boot event; physical keys remain unverified')
