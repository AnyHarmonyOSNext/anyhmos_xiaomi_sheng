"""Persist tested DE wrapping for the original distributed database service."""
from pathlib import Path
import shutil
r=Path(__file__).resolve().parent.parent
d=r/'compat/sheng-graphics/v114';assert not d.exists()
shutil.copytree(r/'compat/sheng-graphics/v113',d)
for p in list(d.iterdir()):
    if p.is_file() and p.suffix in {'.cfg','.sh'}:
        q=p.with_name(p.name.replace('v113','v114'))
        s=p.read_text(encoding='utf-8').replace('v113','v114')
        if p!=q:p.unlink()
        q.write_text(s,encoding='utf-8',newline='\n')
for name in ['hmos_probe_v113.c','probe_graphics_v113.inc','probe_command_v113.inc',
             'build_probe_v113.py','verify_v113.py','start_native_desktop_v113.sh']:
    (r/'tools'/name.replace('v113','v114')).write_text(
        (r/'tools'/name).read_text(encoding='utf-8').replace('v113','v114'),encoding='utf-8',newline='\n')
for name in ['init-core-v113.cfg','sheng-graphics-v113.hcs']:
    p=r/'tools/configs'/name;q=p.with_name(name.replace('v113','v114'))
    if p.suffix=='.cfg':q.write_text(p.read_text(encoding='utf-8').replace('v113','v114'),encoding='utf-8',newline='\n')
    else:shutil.copy2(p,q)
(d/'apply-db-key-v1.sh').unlink()
for name in ['libdbkeys.so','apply-db-key-v2.sh']:
    shutil.copy2(r/'compat/sheng-framework/db-key-v2'/name,d/name)
p=d/'apply-runtime-v114.sh'
p.write_text(p.read_text(encoding='utf-8').replace('apply-db-key-v1.sh','apply-db-key-v2.sh'),encoding='utf-8',newline='\n')
p=r/'tools/verify_v114.py';s=p.read_text(encoding='utf-8')
s=s.replace('compat/sheng-framework/db-key-v1','compat/sheng-framework/db-key-v2').replace('apply-db-key-v1.sh','apply-db-key-v2.sh')
marker=" assert b'start-wifi-v114.sh' in binary"
assert s.count(marker)==1
s=s.replace(marker," assert 'graphics/apply-db-key-v1.sh' not in new\n assert b'libdistributeddatasvcfwk.z.so' in new['graphics/apply-db-key-v2.sh'][1]\n"+marker)
p.write_text(s,encoding='utf-8',newline='\n')
print('v114 prepared: tested DE CryptoManager route, original other HUKS calls, no audio/DSP autostart')
