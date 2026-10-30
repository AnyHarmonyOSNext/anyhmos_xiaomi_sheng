"""Restore original resource limits; native token service and capture-only role."""
from pathlib import Path
import shutil,json
r=Path(__file__).resolve().parent.parent
for name in ['hmos_probe.c','probe_graphics.inc','probe_command.inc']:shutil.copy2(r/'tools'/name,r/'tools/archive'/(Path(name).stem+'_v41'+Path(name).suffix))
p=r/'tools/hmos_probe.c';p.write_text(p.read_text().replace('v41','v42'))
cfg=json.loads((r/'tools/configs/init-core-v41.cfg').read_text())
pre=next(j for j in cfg['jobs'] if j['name']=='pre-init')
original=json.loads((r/'work/hmos_system/system/system/etc/init.cfg').read_text())
original_limits=[c for j in original['jobs'] for c in j['cmds'] if c.startswith('setrlimit ')]
assert 'setrlimit RLIMIT_NICE 40 40' in original_limits and 'setrlimit RLIMIT_NOFILE 32768 32768' in original_limits
pre['cmds']=original_limits+pre['cmds']
access=json.loads((r/'work/hmos_system/system/system/etc/init/access_token.cfg').read_text())
service=access['services'][0];service={k:v for k,v in service.items() if k not in ['critical','jobs','writepid']}
service.update({'disabled':1,'once':1,'start-mode':'condition','sandbox':0,'saspawn':False})
cfg['services'].append(service)
prep=[c for j in access['jobs'] if j['name']=='post-fs-data' for c in j['cmds'] if c.startswith('mkdir /data/')]
gate=next(j for j in cfg['jobs'] if j['name']=='param:sheng-debug-coredeps')
gate['cmds']=prep+gate['cmds']+['start accesstoken_service']
cfg['services'].append({'name':'sheng_snapshot','path':['/system/bin/snapshot_display','-i','0','-f','/data/local/tmp/sheng-capture/display0.jpeg'],'uid':'shell','gid':['shell'],'permission':['ohos.permission.CAPTURE_SCREEN'],'disabled':1,'once':1,'start-mode':'condition','sandbox':0})
cfg['jobs'].append({'name':'param:sheng-debug-capture','condition':'sheng.debug.start.capture=true','cmds':['mkdir /data/local/tmp/sheng-capture 0755 shell shell','setparam const.security.developermode.state true','start sheng_snapshot']})
raw=(json.dumps(cfg,indent=2)+'\n').encode();assert len(raw)<32768
(r/'tools/configs/init-core-v42.cfg').write_bytes(raw)
shutil.copytree(r/'compat/sheng-graphics/v41',r/'compat/sheng-graphics/v42',dirs_exist_ok=True)
(r/'tools/build_probe_v42.py').write_text((r/'tools/build_probe_v41.py').read_text().replace('v41','v42'))
s=(r/'tools/verify_v41.py').read_text().replace('v41','v42').replace("'render_service','foundation'}","'render_service','foundation','accesstoken_service','sheng_snapshot'}")
(r/'tools/verify_v42.py').write_text(s)
(r/'analysis/v42-native-inputs.json').write_text(json.dumps({'status':'candidate_not_flashed','config_bytes':len(raw),'resource_limits':original_limits,'token_service_native_uid':service['uid'],'snapshot_role':cfg['services'][-1],'notes':'Snapshot is an explicit one-shot role with only CAPTURE_SCREEN; actual native init/token manager policy is used. No permission checks/token IDs/kernel APIs are forged.'},indent=2)+'\n')
print('v42 config bytes',len(raw),'original limits',original_limits)
