"""Adapt the native root to the user's five-partition super with preload."""
from pathlib import Path
import shutil
r=Path(__file__).resolve().parent.parent
d=r/'compat/sheng-graphics/v92'
assert not d.exists()
shutil.copytree(r/'compat/sheng-graphics/v91',d)
for p in list(d.iterdir()):
    if p.is_file() and p.suffix in {'.sh','.cfg'}:
        q=p.with_name(p.name.replace('v91','v92'))
        s=p.read_text(encoding='utf-8').replace('v91','v92').replace('V91','V92')
        if q!=p:p.unlink()
        q.write_text(s,encoding='utf-8',newline='\n')
for n in ['hmos_probe_v91.c','probe_graphics_v91.inc','probe_command_v91.inc',
          'build_probe_v91.py','verify_v91.py','start_native_desktop_v91.sh']:
    s=(r/'tools'/n).read_text(encoding='utf-8').replace('v91','v92')
    (r/'tools'/n.replace('v91','v92')).write_text(s,encoding='utf-8',newline='\n')
(r/'tools/configs/init-core-v92.cfg').write_text(
    (r/'tools/configs/init-core-v91.cfg').read_text(encoding='utf-8').replace('v91','v92'),
    encoding='utf-8',newline='\n')
print('v92 baseline staged; apply reviewed new-layout source changes before build')
