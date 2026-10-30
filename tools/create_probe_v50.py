"""Gate the donor's original accountmgr and appspawn for app-framework bring-up."""
from pathlib import Path
import json,shutil
r=Path(__file__).resolve().parent.parent
for name in ['hmos_probe.c','probe_graphics.inc','probe_command.inc']:
    archive=r/'tools/archive'/(Path(name).stem+'_v49'+Path(name).suffix)
    if not archive.exists():shutil.copy2(r/'tools'/name,archive)
shutil.copytree(r/'compat/sheng-graphics/v49',r/'compat/sheng-graphics/v50',dirs_exist_ok=True)
c=(r/'tools/archive/hmos_probe_v49.c').read_text().replace('v49','v50')
old='"/hmos-root/data/storage/el2"};'
assert c.count(old)==1
c=c.replace(old,'"/hmos-root/data/storage/el2","/hmos-root/data/service/el1/public/for-all-app","/hmos-root/data/service/el1/startup"};')
(r/'tools/hmos_probe.c').write_text(c)
cfg=json.loads((r/'tools/configs/init-core-v49.cfg').read_text())
report={'version':'v50','state':'OFFLINE_CANDIDATE_NOT_FLASHED','native_services':[]}
for name,gate in [('accountmgr','account'),('appspawn','appspawn')]:
    original=json.loads((r/f'work/hmos_system/system/system/etc/init/{name}.cfg').read_text())
    service=next(s for s in original['services'] if s['name']==name).copy()
    removed={key:service.pop(key) for key in ['critical','writepid','on-restart','jobs','ondemand'] if key in service}
    service.update(disabled=1,once=1,saspawn=False)
    service['start-mode']='condition'
    if name=='appspawn':service['cgroup']=False
    cfg['services'].append(service)
    # Only the original mkdir commands are selected, not unrelated hardware
    # mounts or cgroup changes. Native UID/GID/token/socket/path stay intact.
    dirs=[cmd for job in original.get('jobs',[]) for cmd in job['cmds'] if cmd.startswith('mkdir ')]
    data_job=f'sheng-{gate}-data'
    cfg['jobs'].append({'name':data_job,'cmds':dirs})
    cfg['jobs'].append({'name':f'param:sheng-debug-{gate}',
        'condition':f'sheng.debug.start.{gate}=true','cmds':[f'trigger {data_job}',f'start {name}']})
    report['native_services'].append({'name':name,'service':service,'removed_restart_or_cgroup_targets':removed,'dirs':dirs})
raw=(json.dumps(cfg,indent=2)+'\n').encode()
assert len(raw)<32768
(r/'tools/configs/init-core-v50.cfg').write_bytes(raw)
for a,b in [('build_probe_v49.py','build_probe_v50.py'),('verify_v49.py','verify_v50.py')]:
    text=(r/'tools'/a).read_text().replace('v49','v50')
    if a.startswith('verify_'):
        text=text.replace("'bootanimation','installs'}","'bootanimation','installs','accountmgr','appspawn'}")
    (r/'tools'/b).write_text(text)
report.update(config_bytes=len(raw),rationale='v49 native AccessToken creates actual HAP tokens and its DB; BMS scan proceeds but GetForegroundOsAccountLocalId returns4194322 while original accountmgr is absent.',
    preservation='No vendor changes, original userdata not exposed; no native roles/permission lists/socket identities replaced; developer fsverity compatibility remains explicit.',
    not_done=['v50 cold boot','account service ready','appspawn ready','BMS401 publish completion','SceneBoard desktop'])
(r/'analysis/v50-framework.json').write_text(json.dumps(report,indent=2)+'\n')
print('v50 staged, config bytes',len(raw))
