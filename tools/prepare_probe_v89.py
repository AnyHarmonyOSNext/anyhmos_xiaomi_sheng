from pathlib import Path
import shutil,json
r=Path(__file__).resolve().parent.parent;d=r/'compat/sheng-graphics/v89';assert not d.exists()
shutil.copytree(r/'compat/sheng-graphics/v88',d)
for p in list(d.iterdir()):
 if p.is_file() and p.suffix in {'.sh','.cfg'}:
  q=p.with_name(p.name.replace('v88','v89'));s=p.read_text(encoding='utf-8').replace('v88','v89').replace('V88','V89')
  if q!=p:p.unlink()
  q.write_text(s,encoding='utf-8',newline='\n')
for n in ['hmos_probe_v88.c','probe_graphics_v88.inc','probe_command_v88.inc','build_probe_v88.py','verify_v88.py','start_native_desktop_v88.sh']:
 s=(r/'tools'/n).read_text(encoding='utf-8').replace('v88','v89')
 if n=='verify_v88.py':s=s.replace('framepacing-v1/libdisplay_composer','static144-v1/libdisplay_composer').replace('framepacing-v1/sheng_gpu_policy','static144-v1/sheng_gpu_policy')
 (r/'tools'/n.replace('v88','v89')).write_text(s,encoding='utf-8',newline='\n')
(r/'tools/configs/init-core-v89.cfg').write_text((r/'tools/configs/init-core-v88.cfg').read_text(encoding='utf-8').replace('v88','v89'),encoding='utf-8',newline='\n')
for n in ['libdisplay_composer_vdi_impl.z.so','sheng_gpu_policy']:shutil.copy2(r/'compat/sheng-graphics/static144-v1'/n,d/n)
p=d/'init-desktop-services.cfg';c=json.loads(p.read_text(encoding='utf-8'))
job=next(j for j in c['jobs'] if j['name']=='sheng-gpu-policy');job['name']='param:sheng-gpu-policy'
svc=next(s for s in c['services'] if s['name']=='sheng_gpu_policy');svc['saspawn']=False
p.write_text(json.dumps(c,indent=2)+'\n',encoding='utf-8',newline='\n')
print('v89 staged: native144 initial OFF->ON, corrected param job + explicit saspawn=false')
