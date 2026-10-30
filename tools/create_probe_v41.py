"""Explicit direct native scheduler and minimal original display-manager SA."""
from pathlib import Path
import shutil,json
r=Path(__file__).resolve().parent.parent
for name in ['hmos_probe.c','probe_graphics.inc','probe_command.inc']:shutil.copy2(r/'tools'/name,r/'tools/archive'/(Path(name).stem+'_v40'+Path(name).suffix))
p=r/'tools/hmos_probe.c';s=p.read_text().replace('v40','v41').replace('char cfg[16384]','char cfg[32768]');p.write_text(s)
cfg=json.loads((r/'tools/configs/init-core-v40.cfg').read_text())
for service in cfg['services']:
    if service['path'][0]=='/system/bin/sa_main':service['saspawn']=False
original=json.loads((r/'work/hmos_system/system/system/etc/init/foundation.cfg').read_text())
f=next(s for s in original['services'] if s['name']=='foundation')
f={k:v for k,v in f.items() if k not in ['critical','jobs','writepid']}
f.update({'disabled':1,'once':1,'start-mode':'condition','sandbox':0,'saspawn':False})
cfg['services'].append(f)
dirs=[cmd for job in original['jobs'] if job['name']=='services:foundation' for cmd in job['cmds'] if cmd.startswith('mkdir /data/')]
cfg['jobs'] += [{'name':'sheng-screen-data','cmds':dirs},{'name':'param:sheng-debug-screen','condition':'sheng.debug.start.screen=true','cmds':['trigger sheng-screen-data','start foundation']}]
raw=(json.dumps(cfg,indent=2)+'\n').encode();assert len(raw)<32768
(r/'tools/configs/init-core-v41.cfg').write_bytes(raw)
dst=r/'compat/sheng-graphics/v41';shutil.copytree(r/'compat/sheng-graphics/v40',dst,dirs_exist_ok=True)
profile=json.loads((r/'work/hmos_system/system/system/profile/foundation.json').read_text())
profile['systemability']=[s for s in profile['systemability'] if s['name']==4607]
assert len(profile['systemability'])==1 and profile['process']=='foundation'
(dst/'foundation-screen-only.json').write_bytes((json.dumps(profile,indent=2)+'\n').encode())
p=r/'tools/probe_graphics.inc';s=p.read_text();needle='    DIR *firmware=opendir("/stock-gpu-firmware");';assert needle in s
s=s.replace(needle,'    if(copy_ram_asset("/graphics/foundation-screen-only.json","/hmos-root/system/profile/foundation.json",0644)<0)return -1;\n'+needle);p.write_text(s)
(r/'tools/build_probe_v41.py').write_text((r/'tools/build_probe_v40.py').read_text().replace('v40','v41'))
s=(r/'tools/verify_v40.py').read_text().replace('v40','v41')
s=s.replace("'concurrent_task_service','render_service'}","'concurrent_task_service','render_service','foundation'}")
(r/'tools/verify_v41.py').write_text(s)
(r/'analysis/v41-native-inputs.json').write_text(json.dumps({'config_bytes':len(raw),'foundation_uid':f['uid'],'foundation_groups':f['gid'],'foundation_permission_count':len(f.get('permission',[])),'profile':profile,'saspawn':False,'saspawn_source_reference':'openharmony/startup_init 970d25f5bda91afa7e02fce69d134b716d0b141d services/init/init_service_manager.c GetServiceSaspawn default enabled for sa_main','status':'candidate_not_flashed'},indent=2)+'\n')
print('v41 config bytes',len(raw),'foundation UID',f['uid'],'permissions',len(f.get('permission',[])))
