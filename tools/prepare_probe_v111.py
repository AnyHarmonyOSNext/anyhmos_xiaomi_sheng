"""Persist the measured 4 s -> 100 ms optional CLI client wait reduction."""
from pathlib import Path
import shutil
r = Path(__file__).resolve().parent.parent
d = r/'compat/sheng-graphics/v111'
assert not d.exists()
shutil.copytree(r/'compat/sheng-graphics/v110', d)
for p in list(d.iterdir()):
    if p.is_file() and p.suffix in {'.cfg', '.sh'}:
        q = p.with_name(p.name.replace('v110','v111'))
        s = p.read_text(encoding='utf-8').replace('v110','v111')
        if p != q: p.unlink()
        q.write_text(s,encoding='utf-8',newline='\n')
for name in ['hmos_probe_v110.c','probe_graphics_v110.inc','probe_command_v110.inc',
             'build_probe_v110.py','verify_v110.py','start_native_desktop_v110.sh']:
    (r/'tools'/name.replace('v110','v111')).write_text(
        (r/'tools'/name).read_text(encoding='utf-8').replace('v110','v111'),encoding='utf-8',newline='\n')
for name in ['init-core-v110.cfg','sheng-graphics-v110.hcs']:
    p=r/'tools/configs'/name;q=p.with_name(name.replace('v110','v111'))
    if p.suffix=='.cfg': q.write_text(p.read_text(encoding='utf-8').replace('v110','v111'),encoding='utf-8',newline='\n')
    else: shutil.copy2(p,q)
shutil.copy2(r/'compat/sheng-framework/cli-wait-v1/apply-cli-wait-v1.sh',d/'apply-cli-wait-v1.sh')
p=d/'apply-runtime-v111.sh'
p.write_text(p.read_text(encoding='utf-8')+'\n$B sh /graphics/apply-cli-wait-v1.sh\n',encoding='utf-8',newline='\n')
p=r/'tools/verify_v111.py';s=p.read_text(encoding='utf-8')
marker=" assert b'start-wifi-v111.sh' in binary"
assert s.count(marker)==1
s=s.replace(marker," assert new['graphics/apply-cli-wait-v1.sh'][1]==(root/'compat/sheng-framework/cli-wait-v1/apply-cli-wait-v1.sh').read_bytes()\n assert b'apply-cli-wait-v1.sh' in new['graphics/apply-runtime-v111.sh'][1]\n"+marker)
p.write_text(s,encoding='utf-8',newline='\n')
print('v111 prepared; original CLI async call/callback/result retained, wait bounded')
