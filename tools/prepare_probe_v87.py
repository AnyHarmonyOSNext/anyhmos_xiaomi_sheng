"""Stage the donor's 16-bit HDI backlight contract, preserving v86."""
from pathlib import Path
import shutil

r = Path(__file__).resolve().parent.parent
d = r/'compat/sheng-graphics/v87'
assert not d.exists()
shutil.copytree(r/'compat/sheng-graphics/v86', d)
for p in list(d.iterdir()):
    if p.is_file() and p.suffix in {'.sh', '.cfg'}:
        dest = p.with_name(p.name.replace('v86', 'v87'))
        s = p.read_text(encoding='utf-8').replace('v86', 'v87').replace('V86', 'V87')
        if dest != p:
            p.unlink()
        dest.write_text(s, encoding='utf-8', newline='\n')
for name in ['hmos_probe_v86.c', 'probe_graphics_v86.inc', 'probe_command_v86.inc',
             'build_probe_v86.py', 'verify_v86.py', 'start_native_desktop_v86.sh']:
    p = r/'tools'/name
    s = p.read_text(encoding='utf-8').replace('v86', 'v87')
    if name == 'verify_v86.py':
        s = s.replace('composer-metrics-v1/libdisplay_composer', 'brightness-v2/libdisplay_composer')
    p.with_name(name.replace('v86','v87')).write_text(s, encoding='utf-8', newline='\n')
(r/'tools/configs/init-core-v87.cfg').write_text(
    (r/'tools/configs/init-core-v86.cfg').read_text(encoding='utf-8').replace('v86','v87'),
    encoding='utf-8', newline='\n')
print('v87 staged; no mode or GPU policy changes')
