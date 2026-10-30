"""Add the donor HUKS service needed by actual account-info digest failures."""
from pathlib import Path
import shutil,json
r=Path(__file__).resolve().parent.parent
for name in ['hmos_probe.c','probe_graphics.inc','probe_command.inc']:
    archive=r/'tools/archive'/(Path(name).stem+'_v50'+Path(name).suffix)
    if not archive.exists():shutil.copy2(r/'tools'/name,archive)
shutil.copytree(r/'compat/sheng-graphics/v50',r/'compat/sheng-graphics/v51',dirs_exist_ok=True)
c=(r/'tools/archive/hmos_probe_v50.c').read_text().replace('v50','v51')
old='"/hmos-root/data/service/el1/startup"};'
assert c.count(old)==1
c=c.replace(old,'"/hmos-root/data/service/el1/startup","/hmos-root/data/data"};')
(r/'tools/hmos_probe.c').write_text(c)
cfg=json.loads((r/'tools/configs/init-core-v50.cfg').read_text())
original=json.loads((r/'work/hmos_system/system/system/etc/init/huks_service.cfg').read_text())
service=original['services'][0].copy()
assert service['name']=='huks_service'
service.update(disabled=1,once=1,saspawn=False)
cfg['services'].append(service)
# Do not execute the donor migration tool on real user data. Only RAM mkdirs.
dirs=[cmd for j in original['jobs'] for cmd in j['cmds'] if cmd.startswith('mkdir ')]
cfg['jobs'].append({'name':'sheng-huks-data','cmds':dirs})
cfg['jobs'].append({'name':'param:sheng-debug-huks','condition':'sheng.debug.start.huks=true',
 'cmds':['trigger sheng-huks-data','start huks_service']})
raw=(json.dumps(cfg,indent=2)+'\n').encode()
assert len(raw)<32768
(r/'tools/configs/init-core-v51.cfg').write_bytes(raw)
for a,b in [('build_probe_v50.py','build_probe_v51.py'),('verify_v50.py','verify_v51.py')]:
    text=(r/'tools'/a).read_text().replace('v50','v51')
    if a.startswith('verify_'):text=text.replace("'accountmgr','appspawn'}","'accountmgr','appspawn','huks_service'}")
    (r/'tools'/b).write_text(text)
(r/'analysis/v51-framework.json').write_text(json.dumps({'version':'v51','status':'OFFLINE_CANDIDATE_NOT_FLASHED',
 'evidence':'v50 accountmgr3058 reports HUKS ClientInit send failure and account digest failure; account.ready=false. appspawn socket exists and started=true; no app spawned.',
 'native_service':service,'dirs':dirs,'config_bytes':len(raw),
 'limits':'Only original service startup tested next. No software HUKS shim, fake account, TEE keys, user authentication or desktop acceptance claimed. No vendor changes.'},indent=2)+'\n')
print('v51 config bytes',len(raw))
