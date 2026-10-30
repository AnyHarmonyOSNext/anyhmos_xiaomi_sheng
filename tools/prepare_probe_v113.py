"""Persist the measured audio policy wait budget without audio autostart."""
from pathlib import Path
import shutil

r = Path(__file__).resolve().parent.parent
d = r / 'compat/sheng-graphics/v113'
assert not d.exists()
shutil.copytree(r / 'compat/sheng-graphics/v112', d)
for p in list(d.iterdir()):
    if p.is_file() and p.suffix in {'.cfg', '.sh'}:
        q = p.with_name(p.name.replace('v112', 'v113'))
        s = p.read_text(encoding='utf-8').replace('v112', 'v113')
        if p != q:
            p.unlink()
        q.write_text(s, encoding='utf-8', newline='\n')
for name in ['hmos_probe_v112.c', 'probe_graphics_v112.inc', 'probe_command_v112.inc',
             'build_probe_v112.py', 'verify_v112.py', 'start_native_desktop_v112.sh']:
    (r / 'tools' / name.replace('v112', 'v113')).write_text(
        (r / 'tools' / name).read_text(encoding='utf-8').replace('v112', 'v113'),
        encoding='utf-8', newline='\n')
for name in ['init-core-v112.cfg', 'sheng-graphics-v112.hcs']:
    p = r / 'tools/configs' / name
    q = p.with_name(name.replace('v112', 'v113'))
    if p.suffix == '.cfg':
        q.write_text(p.read_text(encoding='utf-8').replace('v112', 'v113'), encoding='utf-8', newline='\n')
    else:
        shutil.copy2(p, q)
shutil.copy2(r / 'compat/sheng-framework/audio-wait-v1/apply-audio-wait-v1.sh', d / 'apply-audio-wait-v1.sh')
p = d / 'apply-runtime-v113.sh'
p.write_text(p.read_text(encoding='utf-8') + '\n$B sh /graphics/apply-audio-wait-v1.sh\n', encoding='utf-8', newline='\n')
p = r / 'tools/verify_v113.py'
s = p.read_text(encoding='utf-8')
marker = " assert b'start-wifi-v113.sh' in binary"
assert s.count(marker) == 1
s = s.replace(marker, " assert new['graphics/apply-audio-wait-v1.sh'][1]==(root/'compat/sheng-framework/audio-wait-v1/apply-audio-wait-v1.sh').read_bytes()\n assert b'apply-audio-wait-v1.sh' in new['graphics/apply-runtime-v113.sh'][1]\n assert b'sheng.debug.start.audio true' not in new['graphics/start-native-desktop-v113.sh'][1]\n" + marker)
p.write_text(s, encoding='utf-8', newline='\n')
print('v113 prepared: measured 400 ms audio wait; audio/DSP remain off; DB wrapping retained')
