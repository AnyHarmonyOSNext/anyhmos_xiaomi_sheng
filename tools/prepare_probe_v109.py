"""Persist the hot-tested native MemMgr optional-Hyperhold port."""
from pathlib import Path
import json
import shutil

r = Path(__file__).resolve().parent.parent
d = r / 'compat/sheng-graphics/v109'
assert not d.exists()
shutil.copytree(r / 'compat/sheng-graphics/v108', d)
for p in list(d.iterdir()):
    if p.is_file() and p.suffix in {'.cfg', '.sh'}:
        q = p.with_name(p.name.replace('v108', 'v109'))
        data = p.read_text(encoding='utf-8').replace('v108', 'v109')
        if q != p:
            p.unlink()
        q.write_text(data, encoding='utf-8', newline='\n')
for name in ['hmos_probe_v108.c', 'probe_graphics_v108.inc', 'probe_command_v108.inc',
             'build_probe_v108.py', 'verify_v108.py', 'start_native_desktop_v108.sh']:
    (r / 'tools' / name.replace('v108', 'v109')).write_text(
        (r / 'tools' / name).read_text(encoding='utf-8').replace('v108', 'v109'),
        encoding='utf-8', newline='\n')
for name in ['init-core-v108.cfg', 'sheng-graphics-v108.hcs']:
    src = r / 'tools/configs' / name
    if src.suffix == '.cfg':
        src.with_name(name.replace('v108', 'v109')).write_text(
            src.read_text(encoding='utf-8').replace('v108', 'v109'),
            encoding='utf-8', newline='\n')
    else:
        shutil.copy2(src, src.with_name(name.replace('v108', 'v109')))
shutil.copy2(r / 'compat/sheng-framework/memmgr-v1/apply-memmgr-v1.sh', d / 'apply-memmgr-v1.sh')
p = d / 'apply-runtime-v109.sh'
s = p.read_text(encoding='utf-8') + '\n$B sh /graphics/apply-memmgr-v1.sh\n'
p.write_text(s, encoding='utf-8', newline='\n')

# Optional diagnostic only. The actual service keeps its original definition.
# Init assigns this diagnostic its own native token; raw root queries correctly
# failed permission checks and are not treated as successful IPC validation.
p = d / 'init-platform-v109.cfg'
cfg = json.loads(p.read_text(encoding='utf-8'))
cfg['services'].append(dict(name='sheng_memmgr_check',
    path=['/data/local/tmp/native_memmgr_readonly', '--service-output'],
    uid='shell', gid=['shell'], permission=['ohos.permission.DUMP'],
    permission_acls=['ohos.permission.DUMP'], disabled=1, once=1,
    sandbox=0, saspawn=False, **{'start-mode': 'condition'}))
cfg['jobs'].append(dict(name='param:sheng-memmgr-check',
    condition='sheng.debug.test.memmgr=true', cmds=['start sheng_memmgr_check']))
p.write_text(json.dumps(cfg, indent=2) + '\n', encoding='utf-8', newline='\n')
p = r / 'tools/verify_v109.py'
s = p.read_text(encoding='utf-8').replace("'time_service','memmgrservice'}", "'time_service','memmgrservice','sheng_memmgr_check'}")
marker = " assert b'start-wifi-v109.sh' in binary"
assert s.count(marker) == 1
s = s.replace(marker, " assert new['graphics/apply-memmgr-v1.sh'][1]==(root/'compat/sheng-framework/memmgr-v1/apply-memmgr-v1.sh').read_bytes()\n"
    + " assert b'apply-memmgr-v1.sh' in new['graphics/apply-runtime-v109.sh'][1]\n"
    + " assert next(x for x in platform['services'] if x['name']=='sheng_memmgr_check')['permission_acls']==['ohos.permission.DUMP']\n"
    + marker)
p.write_text(s, encoding='utf-8', newline='\n')
print('v109 prepared: guarded four-byte optional-Hyperhold port and opt-in native diagnostic')
