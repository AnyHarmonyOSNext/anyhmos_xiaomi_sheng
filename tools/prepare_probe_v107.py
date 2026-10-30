"""Use complete mkdir arguments: the donor migration hook calls strlen(argv[2])."""
from pathlib import Path
import json
import shutil
r=Path(__file__).resolve().parent.parent
d=r/'compat/sheng-graphics/v107'
assert not d.exists()
shutil.copytree(r/'compat/sheng-graphics/v106',d)
for p in list(d.iterdir()):
    if p.is_file() and p.suffix in {'.cfg','.sh'}:
        q=p.with_name(p.name.replace('v106','v107'))
        data=p.read_text(encoding='utf-8').replace('v106','v107')
        if q!=p:p.unlink()
        q.write_text(data,encoding='utf-8',newline='\n')
for name in ['hmos_probe_v106.c','probe_graphics_v106.inc','probe_command_v106.inc',
             'build_probe_v106.py','verify_v106.py','start_native_desktop_v106.sh']:
    (r/'tools'/name.replace('v106','v107')).write_text(
        (r/'tools'/name).read_text(encoding='utf-8').replace('v106','v107'),newline='\n')
for name in ['init-core-v106.cfg','sheng-graphics-v106.hcs']:
    src=r/'tools/configs'/name
    if src.suffix=='.cfg':
        src.with_name(name.replace('v106','v107')).write_text(src.read_text().replace('v106','v107'),newline='\n')
    else:shutil.copy2(src,src.with_name(name.replace('v106','v107')))
p=d/'init-platform-v107.cfg'
cfg=json.loads(p.read_text())
job=next(x for x in cfg['jobs'] if x['name']=='param:sheng-memmgr')
job['cmds']=['mkdir /data/service/el1/public/memmgr 0775 memmgr memmgr',
             'restorecon /data/service/el1/public/memmgr', 'start memmgrservice']
p.write_text(json.dumps(cfg,indent=2)+'\n',newline='\n')
p=r/'tools/verify_v107.py'
s=p.read_text()
marker=" assert b'start-wifi-v107.sh' in binary"
assert s.count(marker)==1
s=s.replace(marker," memjob=next(x for x in platform['jobs'] if x['name']=='param:sheng-memmgr')\n"
    +" assert memjob['cmds'][0]=='mkdir /data/service/el1/public/memmgr 0775 memmgr memmgr'\n"
    +" assert all(len(c.split())>=5 for c in memjob['cmds'] if c.startswith('mkdir '))\n"+marker)
p.write_text(s,newline='\n')
print('v107: guard complete MemMgr mkdir arguments; preserve v106 time clock port')
