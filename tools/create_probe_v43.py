"""Register original bootanimation identity; leave render callback DSO original."""
from pathlib import Path
import shutil,json
r=Path(__file__).resolve().parent.parent
for name in ['hmos_probe.c','probe_graphics.inc','probe_command.inc']:
 archived=r/'tools/archive'/(Path(name).stem+'_v42'+Path(name).suffix)
 if not archived.exists():shutil.copy2(r/'tools'/name,archived)
p=r/'tools/hmos_probe.c';p.write_text(p.read_text().replace('v42','v43'))
cfg=json.loads((r/'tools/configs/init-core-v42.cfg').read_text())
service=json.loads((r/'work/hmos_system/system/system/etc/init/bootanimation.cfg').read_text())['services'][0]
service.update({'disabled':1,'once':1,'start-mode':'condition','sandbox':0,'saspawn':False})
cfg['services'].append(service)
cfg['jobs'] += [
 {'name':'param:sheng-debug-bootanim-start','condition':'sheng.debug.start.bootanim=true','cmds':['start bootanimation']},
 {'name':'param:sheng-debug-bootanim-stop','condition':'sheng.debug.start.bootanim=false','cmds':['stop bootanimation']}]
raw=(json.dumps(cfg,indent=2)+'\n').encode();assert len(raw)<32768
(r/'tools/configs/init-core-v43.cfg').write_bytes(raw)
shutil.copytree(r/'compat/sheng-graphics/v42',r/'compat/sheng-graphics/v43',dirs_exist_ok=True)
(r/'tools/build_probe_v43.py').write_text((r/'tools/build_probe_v42.py').read_text().replace('v42','v43'))
(r/'tools/verify_v43.py').write_text((r/'tools/verify_v42.py').read_text().replace('v42','v43').replace("'sheng_snapshot'}","'sheng_snapshot','bootanimation'}"))
(r/'analysis/v43-native-inputs.json').write_text(json.dumps({'status':'candidate_not_flashed','config_bytes':len(raw),'bootanimation_original_role':service,'render_callback_library':'original; no callback patch bundled','test':'Native init role vs previous unregistered root diagnostic; keep original server token checks'},indent=2)+'\n')
print('v43 config bytes',len(raw))
