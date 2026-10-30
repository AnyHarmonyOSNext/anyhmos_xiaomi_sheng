"""Offline next-step candidate: original installs SA511, explicitly gated."""
from pathlib import Path
import shutil,json
r=Path(__file__).resolve().parent.parent
for name in ['hmos_probe.c','probe_graphics.inc','probe_command.inc']:
 dst=r/'tools/archive'/(Path(name).stem+'_v44'+Path(name).suffix)
 if not dst.exists():shutil.copy2(r/'tools'/name,dst)
p=r/'tools/hmos_probe.c';p.write_text(p.read_text(encoding='utf-8').replace('v44','v45'),encoding='utf-8')
cfg=json.loads((r/'tools/configs/init-core-v44.cfg').read_text(encoding='utf-8'))
service=json.loads((r/'work/hmos_system/system/system/etc/init/installs.cfg').read_text(encoding='utf-8'))['services'][0]
service.pop('ondemand',None)
service.update({'disabled':1,'once':1,'start-mode':'condition','sandbox':0,'saspawn':False,'cgroup':False})
cfg['services'].append(service)
cfg['jobs'].append({'name':'param:sheng-debug-installs','condition':'sheng.debug.start.installs=true','cmds':['start installs']})
(r/'tools/configs/init-core-v45.cfg').write_text(json.dumps(cfg,indent=2)+'\n',encoding='utf-8')
dst=r/'compat/sheng-graphics/v45';shutil.copytree(r/'compat/sheng-graphics/v44',dst,dirs_exist_ok=True)
profile=json.loads((r/'work/hmos_system/system/system/profile/installs.json').read_text(encoding='utf-8'))
assert len(profile['systemability'])==1 and profile['systemability'][0]['name']==511
profile['systemability'][0]['run-on-create']=True
(dst/'installs-debug-start.json').write_text(json.dumps(profile,indent=2)+'\n',encoding='utf-8')
shutil.copy2(r/'compat/sheng-framework/foundation-app-core-v1.json',dst/'foundation-app-core.json')
shutil.copy2(r/'work/capture_scanout',dst/'capture_scanout')
g=(r/'tools/archive/probe_graphics_v44.inc').read_text(encoding='utf-8')
needle='    DIR *firmware=opendir("/stock-gpu-firmware");';assert needle in g
g=g.replace(needle,'''    if(copy_ram_asset("/graphics/installs-debug-start.json","/hmos-root/system/profile/installs.json",0644)<0||
       copy_ram_asset("/graphics/foundation-app-core.json","/hmos-root/data/local/tmp/foundation-app-core.json",0644)<0||
       copy_ram_asset("/graphics/capture_scanout","/hmos-root/data/local/tmp/sheng-graphics/capture_scanout",0755)<0)return -1;
'''+needle)
(r/'tools/probe_graphics.inc').write_text(g,encoding='utf-8')
(r/'tools/build_probe_v45.py').write_text((r/'tools/build_probe_v44.py').read_text(encoding='utf-8').replace('v44','v45'),encoding='utf-8')
(r/'tools/verify_v45.py').write_text((r/'tools/verify_v44.py').read_text(encoding='utf-8').replace('v44','v45').replace("'bootanimation'}","'bootanimation','installs'}"),encoding='utf-8')
report={'status':'OFFLINE_CANDIDATE_NOT_FLASHED','native_service':service,'profile':profile,'rationale':'Bounded app-core test PID989: BMS SA401 waits repeatedly for SA511 then CreateBmsServiceDir fails. Original donor calls the service installs with SA511/libinstalls.z.so, not a missing installd.cfg.',
 'diagnostic_changes':'Keep original uid/gid/caps/kernel_permission/secon; explicit once/disabled gate, remove ondemand and disable unimplemented cgroup accounting in this isolated test; SA511 run-on-create=true. No desktop acceptance inferred.',
 'next':'First cold validate v45 physical display baseline, then explicit start.installs gate and verify SA511 before retrying bounded foundation-app-core profile. Do not rename legacy libwms to libsms; SceneBoard build excludes legacy libwms.'}
(r/'analysis/v45-native-inputs.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
print('v45 candidate service',service['name'],'uid',service['uid'])
