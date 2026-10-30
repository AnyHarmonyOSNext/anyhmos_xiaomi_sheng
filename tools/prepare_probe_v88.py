"""Stage hardware VSYNC and reversible GPU interaction policy from v87."""
from pathlib import Path
import json,hashlib,shutil
r=Path(__file__).resolve().parent.parent;d=r/'compat/sheng-graphics/v88'
assert not d.exists();shutil.copytree(r/'compat/sheng-graphics/v87',d)
for p in list(d.iterdir()):
 if p.is_file() and p.suffix in {'.sh','.cfg'}:
  q=p.with_name(p.name.replace('v87','v88'));s=p.read_text(encoding='utf-8').replace('v87','v88').replace('V87','V88')
  if q!=p:p.unlink()
  q.write_text(s,encoding='utf-8',newline='\n')
for n in ['hmos_probe_v87.c','probe_graphics_v87.inc','probe_command_v87.inc','build_probe_v87.py','verify_v87.py','start_native_desktop_v87.sh']:
 p=r/'tools'/n;s=p.read_text(encoding='utf-8').replace('v87','v88')
 if n=='verify_v87.py':
  s=s.replace('brightness-v2/libdisplay_composer','framepacing-v1/libdisplay_composer').replace('sheng-touch/service-v1/sheng_thp_bridge','sheng-touch/service-v2/sheng_thp_bridge')
  s=s.replace("'sheng_screen_unlock'}","'sheng_screen_unlock','sheng_gpu_policy'}")
  s=s.replace(" assert b'apply-render-usage.sh'", " assert new['graphics/sheng_gpu_policy'][1]==(root/'compat/sheng-graphics/framepacing-v1/sheng_gpu_policy').read_bytes()\n assert b'apply-render-usage.sh'")
 (r/'tools'/n.replace('v87','v88')).write_text(s,encoding='utf-8',newline='\n')
(r/'tools/configs/init-core-v88.cfg').write_text((r/'tools/configs/init-core-v87.cfg').read_text(encoding='utf-8').replace('v87','v88'),encoding='utf-8',newline='\n')
for name in ['libdisplay_composer_vdi_impl.z.so','sheng_gpu_policy']:
 shutil.copy2(r/'compat/sheng-graphics/framepacing-v1'/name,d/name)
shutil.copy2(r/'compat/sheng-touch/service-v2/sheng_thp_bridge',d/'sheng_thp_bridge')
script=d/'apply-runtime-v88.sh';s=script.read_text(encoding='utf-8')
old=hashlib.sha256((r/'compat/sheng-touch/service-v1/sheng_thp_bridge').read_bytes()).hexdigest()
new=hashlib.sha256((d/'sheng_thp_bridge').read_bytes()).hexdigest();assert old in s;s=s.replace(old,new)
script.write_text(s,encoding='utf-8',newline='\n')
script=d/'apply-hardware-v88.sh';s=script.read_text(encoding='utf-8').replace('hardware_observe native_brightness_launcher','hardware_observe sheng_gpu_policy native_brightness_launcher')
s+='\n: > $R/data/local/tmp/sheng-gpu-policy.txt\n$B chmod 0600 $R/data/local/tmp/sheng-gpu-policy.txt\n$B rm -f $R/data/local/tmp/sheng-gpu-policy-disabled\n'
script.write_text(s,encoding='utf-8',newline='\n')
config=d/'init-desktop-services.cfg';c=json.loads(config.read_text(encoding='utf-8'))
c['jobs'].append({'name':'sheng-gpu-policy','condition':'sheng.debug.start.gpu-policy=true','cmds':['start sheng_gpu_policy']})
c['services'].append({'name':'sheng_gpu_policy','path':['/compat/bin/sheng_gpu_policy'],'uid':'root','gid':['root'],'once':1,'disabled':1,'sandbox':0,'start-mode':'condition'})
# Original init service stderr forwarding is managed by a tiny native launcher.
c['services'][-1]['path']=['/compat/bin/sheng_gpu_policy']
config.write_text(json.dumps(c,indent=2)+'\n',encoding='utf-8',newline='\n')
for script in [d/'start-graphics-v88.sh']:
 s=script.read_text(encoding='utf-8');needle='$B sleep 2\n$B chroot $R /system/bin/param set sheng.debug.start.render true'
 assert s.count(needle)==1
 s=s.replace(needle,'$B chroot $R /system/bin/param set sheng.debug.start.gpu-policy true\n'+needle)
 script.write_text(s,encoding='utf-8',newline='\n')
print('v88 staged: actual hardware vsync, fixed120, GPU adaptive550/idle restore, THP aggregate metrics')
