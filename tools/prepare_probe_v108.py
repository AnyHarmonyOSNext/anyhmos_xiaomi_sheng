"""Avoid donor init's crashing one-argument restorecon command hook.

Keep MemMgr's original identity and explicit directory mode/ownership. Do not
patch the migration library or enable Huawei-only VM tuning jobs.
"""
from pathlib import Path
import json
import shutil

r = Path(__file__).resolve().parent.parent
d = r / 'compat/sheng-graphics/v108'
assert not d.exists()
shutil.copytree(r / 'compat/sheng-graphics/v107', d)
for p in list(d.iterdir()):
    if p.is_file() and p.suffix in {'.cfg', '.sh'}:
        q = p.with_name(p.name.replace('v107', 'v108'))
        data = p.read_text(encoding='utf-8').replace('v107', 'v108')
        if q != p:
            p.unlink()
        q.write_text(data, encoding='utf-8', newline='\n')
for name in ['hmos_probe_v107.c', 'probe_graphics_v107.inc', 'probe_command_v107.inc',
             'build_probe_v107.py', 'verify_v107.py', 'start_native_desktop_v107.sh']:
    (r / 'tools' / name.replace('v107', 'v108')).write_text(
        (r / 'tools' / name).read_text(encoding='utf-8').replace('v107', 'v108'),
        encoding='utf-8', newline='\n')
for name in ['init-core-v107.cfg', 'sheng-graphics-v107.hcs']:
    src = r / 'tools/configs' / name
    if src.suffix == '.cfg':
        src.with_name(name.replace('v107', 'v108')).write_text(
            src.read_text(encoding='utf-8').replace('v107', 'v108'),
            encoding='utf-8', newline='\n')
    else:
        shutil.copy2(src, src.with_name(name.replace('v107', 'v108')))
p = d / 'init-platform-v108.cfg'
cfg = json.loads(p.read_text(encoding='utf-8'))
job = next(x for x in cfg['jobs'] if x['name'] == 'param:sheng-memmgr')
assert job['cmds'] == ['mkdir /data/service/el1/public/memmgr 0775 memmgr memmgr',
                       'restorecon /data/service/el1/public/memmgr', 'start memmgrservice']
job['cmds'].remove('restorecon /data/service/el1/public/memmgr')
p.write_text(json.dumps(cfg, indent=2) + '\n', encoding='utf-8', newline='\n')
p = r / 'tools/verify_v108.py'
s = p.read_text(encoding='utf-8')
marker = " assert b'start-wifi-v108.sh' in binary"
assert s.count(marker) == 1
s = s.replace(marker, " assert memjob['cmds']==['mkdir /data/service/el1/public/memmgr 0775 memmgr memmgr','start memmgrservice']\n" + marker)
p.write_text(s, encoding='utf-8', newline='\n')
print('v108 prepared: omit only crashing init restorecon command; retain native MemMgr')
