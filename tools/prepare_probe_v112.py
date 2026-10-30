"""Persist tested software wrapping only in the original RDB/KV delegates."""
from pathlib import Path
import shutil
r=Path(__file__).resolve().parent.parent
d=r/'compat/sheng-graphics/v112'
assert not d.exists()
shutil.copytree(r/'compat/sheng-graphics/v111',d)
for p in list(d.iterdir()):
    if p.is_file() and p.suffix in {'.cfg','.sh'}:
        q=p.with_name(p.name.replace('v111','v112'))
        s=p.read_text(encoding='utf-8').replace('v111','v112')
        if p!=q:p.unlink()
        q.write_text(s,encoding='utf-8',newline='\n')
for name in ['hmos_probe_v111.c','probe_graphics_v111.inc','probe_command_v111.inc','build_probe_v111.py','verify_v111.py','start_native_desktop_v111.sh']:
    (r/'tools'/name.replace('v111','v112')).write_text((r/'tools'/name).read_text(encoding='utf-8').replace('v111','v112'),encoding='utf-8',newline='\n')
for name in ['init-core-v111.cfg','sheng-graphics-v111.hcs']:
    p=r/'tools/configs'/name;q=p.with_name(name.replace('v111','v112'))
    if p.suffix=='.cfg':q.write_text(p.read_text(encoding='utf-8').replace('v111','v112'),encoding='utf-8',newline='\n')
    else:shutil.copy2(p,q)
for name in ['libdbkeys.so','apply-db-key-v1.sh']:
    shutil.copy2(r/'compat/sheng-framework/db-key-v1'/name,d/name)
p=d/'apply-runtime-v112.sh'
p.write_text(p.read_text(encoding='utf-8')+'\n$B sh /graphics/apply-db-key-v1.sh\n',encoding='utf-8',newline='\n')
# Retire the unplayed diagnostic picture payload to make image space. Original
# real-video configuration stays in sys_prod, with animation still gated off.
for name in ['bootpic.zip','bootanimation-diagnostic.json']:(d/name).unlink()
p=r/'tools/probe_graphics_v112.inc';s=p.read_text(encoding='utf-8')
s=s.replace(',"bootpic.zip"','')
lines=s.splitlines()
lines=[line for line in lines if 'copy_ram_asset("/graphics/bootanimation-diagnostic.json"' not in line and 'copy_ram_asset("/graphics/bootpic.zip"' not in line]
p.write_text('\n'.join(lines)+'\n',encoding='utf-8',newline='\n')
p=r/'tools/verify_v112.py';s=p.read_text(encoding='utf-8')
marker=" assert b'start-wifi-v112.sh' in binary"
assert s.count(marker)==1
s=s.replace(marker," assert new['graphics/libdbkeys.so'][1]==(root/'compat/sheng-framework/db-key-v1/libdbkeys.so').read_bytes()\n assert new['graphics/apply-db-key-v1.sh'][1]==(root/'compat/sheng-framework/db-key-v1/apply-db-key-v1.sh').read_bytes()\n assert b'apply-db-key-v1.sh' in new['graphics/apply-runtime-v112.sh'][1]\n assert 'graphics/bootpic.zip' not in new\n assert b'bootanimation-diagnostic.json' not in binary\n"+marker)
p.write_text(s,encoding='utf-8',newline='\n')
print('v112 prepared: tested per-UID DB wrapping, no audio autostart or vendor changes')
