from pathlib import Path
import shutil
r=Path(__file__).resolve().parent.parent;d=r/'compat/sheng-graphics/v90';assert not d.exists();shutil.copytree(r/'compat/sheng-graphics/v89',d)
for p in list(d.iterdir()):
 if p.is_file() and p.suffix in {'.sh','.cfg'}:
  q=p.with_name(p.name.replace('v89','v90'));s=p.read_text(encoding='utf-8').replace('v89','v90').replace('V89','V90')
  if q!=p:p.unlink()
  q.write_text(s,encoding='utf-8',newline='\n')
for n in ['hmos_probe_v89.c','probe_graphics_v89.inc','probe_command_v89.inc','build_probe_v89.py','verify_v89.py','start_native_desktop_v89.sh']:
 s=(r/'tools'/n).read_text(encoding='utf-8').replace('v89','v90')
 if n=='verify_v89.py':s=s.replace('static144-v1/sheng_gpu_policy','gpu-policy-v2/sheng_gpu_policy')
 (r/'tools'/n.replace('v89','v90')).write_text(s,encoding='utf-8',newline='\n')
(r/'tools/configs/init-core-v90.cfg').write_text((r/'tools/configs/init-core-v89.cfg').read_text(encoding='utf-8').replace('v89','v90'),encoding='utf-8',newline='\n')
shutil.copy2(r/'compat/sheng-graphics/gpu-policy-v2/sheng_gpu_policy',d/'sheng_gpu_policy')
print('v90 stages observer master release; userdata remains file until display test completes')
