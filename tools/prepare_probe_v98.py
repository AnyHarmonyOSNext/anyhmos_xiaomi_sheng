"""Fix the initial DMS wake order and retain the verified native audio policy."""
from pathlib import Path
import shutil

r = Path(__file__).resolve().parent.parent
d = r / 'compat/sheng-graphics/v98'
assert not d.exists()
shutil.copytree(r / 'compat/sheng-graphics/v97', d)
for p in list(d.iterdir()):
    if p.is_file() and p.suffix in {'.sh', '.cfg'}:
        q = p.with_name(p.name.replace('v97', 'v98'))
        s = p.read_text(encoding='utf-8').replace('v97', 'v98').replace('V97', 'V98')
        if q != p:
            p.unlink()
        q.write_text(s, encoding='utf-8', newline='\n')
for name in ['hmos_probe_v97.c', 'probe_graphics_v97.inc', 'probe_command_v97.inc',
             'build_probe_v97.py', 'verify_v97.py', 'start_native_desktop_v97.sh']:
    (r / 'tools' / name.replace('v97', 'v98')).write_text(
        (r / 'tools' / name).read_text(encoding='utf-8').replace('v97', 'v98'),
        encoding='utf-8', newline='\n')
(r / 'tools/configs/init-core-v98.cfg').write_text(
    (r / 'tools/configs/init-core-v97.cfg').read_text(encoding='utf-8').replace('v97', 'v98'),
    encoding='utf-8', newline='\n')
shutil.copyfile(r / 'compat/debug-tools/native_display_wake_v2', d / 'native_display_wake')
for p in [r / 'tools/start_native_desktop_v98.sh', d / 'start-native-desktop-v98.sh']:
    s = p.read_text()
    marker = 'stage=graphics\n'
    assert s.count(marker) == 1
    s = s.replace(marker, '''stage=audio
$B chroot "$R" /system/bin/param set sheng.debug.start.audio true
deadline=$(($(now)+15))
while ! $B timeout 2 $B chroot "$R" /compat/bin/native_sa_check 3009; do
 [ "$(now)" -lt "$deadline" ] || { echo AUTOSTART_AUDIO_POLICY_UNAVAILABLE=1; break; }
 $B sleep 1
done
stage=graphics
''')
    p.write_text(s, encoding='utf-8', newline='\n')
p = r / 'tools/verify_v98.py'
s = p.read_text().replace("assert b'apply-preload.sh' in binary", """assert new['graphics/native_display_wake'][1]==(root/'compat/debug-tools/native_display_wake_v2').read_bytes()
 assert b'AUTOSTART_AUDIO_POLICY_UNAVAILABLE=1' in new['graphics/start-native-desktop-v98.sh'][1]
 assert b'apply-preload.sh' in binary""")
p.write_text(s, encoding='utf-8', newline='\n')
print('v98 staged: wake state before panel power; native audio policy autostart, no GPU changes')
