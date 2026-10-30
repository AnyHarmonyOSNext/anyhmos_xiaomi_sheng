"""Run service directory preparation inline, including on an empty userdata."""
from pathlib import Path
import json
import shutil

r = Path(__file__).resolve().parent.parent
d = r / 'compat/sheng-graphics/v94'
assert not d.exists()
shutil.copytree(r / 'compat/sheng-graphics/v93', d)
for p in list(d.iterdir()):
    if p.is_file() and p.suffix in {'.sh', '.cfg'}:
        q = p.with_name(p.name.replace('v93', 'v94'))
        s = p.read_text(encoding='utf-8').replace('v93', 'v94').replace('V93', 'V94')
        if q != p:
            p.unlink()
        q.write_text(s, encoding='utf-8', newline='\n')
for name in ['hmos_probe_v93.c', 'probe_graphics_v93.inc', 'probe_command_v93.inc',
             'build_probe_v93.py', 'verify_v93.py', 'start_native_desktop_v93.sh']:
    s = (r / 'tools' / name).read_text(encoding='utf-8').replace('v93', 'v94')
    (r / 'tools' / name.replace('v93', 'v94')).write_text(s, encoding='utf-8', newline='\n')
core = r / 'tools/configs/init-core-v94.cfg'
core.write_text((r / 'tools/configs/init-core-v93.cfg').read_text(encoding='utf-8').replace('v93', 'v94'),
                encoding='utf-8', newline='\n')
for p in [core, d / 'init-desktop-services.cfg']:
    config = json.loads(p.read_text(encoding='utf-8'))
    jobs = {job['name']: job for job in config['jobs']}
    consumed = set()
    for job in config['jobs']:
        if not job['name'].startswith('param:'):
            continue
        expanded = []
        for cmd in job['cmds']:
            if cmd.startswith('trigger sheng-'):
                prep = jobs[cmd[8:]]
                consumed.add(prep['name'])
                assert 'condition' not in prep
                assert all(x.startswith(('mkdir ', 'write ')) for x in prep['cmds']), prep['name']
                expanded.extend(prep['cmds'])
            else:
                expanded.append(cmd)
        job['cmds'] = expanded
    config['jobs'] = [j for j in config['jobs'] if j['name'] not in consumed]
    p.write_text(json.dumps(config, ensure_ascii=False, indent=2) + '\n', encoding='utf-8', newline='\n')
# A clean preinstalled-app scan has a different bound from a warm desktop start.
for p in [r / 'tools/start_native_desktop_v94.sh', d / 'start-native-desktop-v94.sh']:
    s = p.read_text(encoding='utf-8').replace('timeout 600 ', 'timeout 900 ')
    s = s.replace('deadline=$(($(now)+120))', 'deadline=$(($(now)+600))')
    p.write_text(s, encoding='utf-8', newline='\n')
p = r / 'tools/hmos_probe_v94.c'
s = p.read_text(encoding='utf-8').replace('"timeout","600"', '"timeout","900"').replace('bounded=600s', 'bounded=900s')
p.write_text(s, encoding='utf-8', newline='\n')
p = r / 'tools/verify_v94.py'
s = p.read_text(encoding='utf-8')
s = s.replace("assert len(new['hmos-init-debug.cfg'][1])<32768", """assert len(new['hmos-init-debug.cfg'][1])<32768
 for checked in [config, json.loads(new['graphics/init-desktop-services.cfg'][1])]:
  assert all(not cmd.startswith('trigger sheng-') for job in checked['jobs'] if job['name'].startswith('param:') for cmd in job['cmds'])
 account_job=next(j for j in config['jobs'] if j['name']=='param:sheng-debug-account')
 assert account_job['cmds'][0]=='mkdir /data/service/el1/public/account 0750 account account'
 assert account_job['cmds'][-1]=='start accountmgr'""")
p.write_text(s, encoding='utf-8', newline='\n')
print('v94 stages directory commands before service starts; no old data and no OOBE completion')
