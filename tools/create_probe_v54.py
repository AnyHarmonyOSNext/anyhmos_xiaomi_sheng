"""Add original storage/KV service gates via a separate private init import."""
from pathlib import Path
import shutil,json,subprocess
r=Path(__file__).resolve().parent.parent
for name in ['hmos_probe.c','probe_graphics.inc','probe_command.inc']:
    p=r/'tools/archive'/(Path(name).stem+'_v53'+Path(name).suffix)
    if not p.exists():shutil.copy2(r/'tools'/name,p)
d=r/'compat/sheng-graphics/v54';shutil.copytree(r/'compat/sheng-graphics/v53',d,dirs_exist_ok=True)
sdk='/root/hmos-work/sdk-6.0.0.47/installed/native/llvm/bin/'
w='/mnt/c/SHENG_WORKSPACE/'
subprocess.run(['wsl','-d','Ubuntu-22.04','-u','root','--',sdk+'clang','--target=aarch64-linux-ohos','-O2','-Wall','-Wextra','-Werror',w+'compat/sheng-framework/account-hmac-v1/storage_ram_launcher.c','-o',w+'compat/sheng-graphics/v54/storage-ram-launcher'],check=True)
subprocess.run(['wsl','-d','Ubuntu-22.04','-u','root','--',sdk+'llvm-strip',w+'compat/sheng-graphics/v54/storage-ram-launcher'],check=True)
extra={'jobs':[],'services':[]}
for name,filename,gate in [('storage_daemon','storage_daemon.cfg','storaged'),('storage_manager','storage_manager.cfg','storage'),('distributeddata','distributed_data.cfg','kvdata')]:
    original=json.loads((r/'work/hmos_system/system/system/etc/init'/filename).read_text())
    s=next(x.copy() for x in original['services'] if x['name']==name)
    for key in ['critical','writepid','jobs','on-restart']:s.pop(key,None)
    s.update(disabled=1,once=1,saspawn=False);s['start-mode']='condition'
    if name=='storage_daemon':s['path']=['/compat/bin/storage-ram-launcher']
    extra['services'].append(s)
    dirs=[x for j in original.get('jobs',[]) for x in j['cmds'] if x.startswith('mkdir ')]
    if name=='storage_daemon':dirs=['mkdir /mnt/data 0755 root root','mkdir /data/service/el1/public/storage_daemon 0755 root root']+dirs
    extra['jobs'].append({'name':'sheng-'+gate+'-data','cmds':dirs})
    extra['jobs'].append({'name':'param:sheng-debug-'+gate,'condition':'sheng.debug.start.'+gate+'=true','cmds':['trigger sheng-'+gate+'-data','start '+name]})
raw=(json.dumps(extra,indent=2)+'\n').encode();assert len(raw)<32768
(d/'init-desktop-services.cfg').write_bytes(raw)
cfg=json.loads((r/'tools/configs/init-core-v53.cfg').read_text());cfg['import']=['/compat/etc/init-desktop-services.cfg']
(r/'tools/configs/init-core-v54.cfg').write_bytes((json.dumps(cfg,indent=2)+'\n').encode())
p=r/'tools/hmos_probe.c';p.write_text(p.read_text().replace('v53','v54'))
g=(r/'tools/probe_graphics.inc').read_text();line='    if(graphics_run_script("/graphics/apply-account-hmac.sh")<0)return -1;'
assert g.count(line)==1
g=g.replace(line,line+'\n    if(copy_ram_asset("/graphics/init-desktop-services.cfg","/hmos-root/compat/etc/init-desktop-services.cfg",0644)<0||copy_ram_asset("/graphics/storage-ram-launcher","/hmos-root/compat/bin/storage-ram-launcher",0755)<0)return -1;')
(r/'tools/probe_graphics.inc').write_text(g)
for stem in ['build_probe','verify']:
    (r/f'tools/{stem}_v54.py').write_text((r/f'tools/{stem}_v53.py').read_text().replace('v53','v54'))
p=r/'tools/verify_v54.py';s=p.read_text();mark=" assert len(new['hmos-init-debug.cfg'][1])<32768"
s=s.replace(mark,mark+"\n assert config['import']==['/compat/etc/init-desktop-services.cfg']\n extra=json.loads(new['graphics/init-desktop-services.cfg'][1]);assert {s['name'] for s in extra['services']}=={'storage_daemon','storage_manager','distributeddata'}\n assert all(s['disabled']==1 and s['once']==1 and 'critical' not in s for s in extra['services'])\n assert next(s for s in extra['services'] if s['name']=='storage_daemon')['path']==['/compat/bin/storage-ram-launcher']")
p.write_text(s)
(r/'analysis/v54-framework.json').write_text(json.dumps({'version':'v54','status':'OFFLINE_CANDIDATE_NOT_FLASHED','reason':'v53 account SA200 and BMS401 registered; account.ready=false. Original OnAddSystemAbility explicitly waits for storage5003 before default account creation. KV1301 is separately gated, not asserted to be the primary blocker.','services':extra,'scope':'RAM data only, no userdata node, storage daemon wrapper denies creation of any block device; original identities and permissions kept; no vendor edits','desktop':False},ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print('extra config bytes',len(raw))
