"""Stage the child-lifecycle fix and an independent native DMS wake service."""
from pathlib import Path
import shutil,json
r=Path(__file__).resolve().parent.parent
d=r/'compat/sheng-graphics/v72'
assert not d.exists()
shutil.copytree(r/'compat/sheng-graphics/v71',d)
for name in ['native_display_wake','capture_scanout']:
 shutil.copy2(r/'compat/debug-tools'/name,d/name)
extra=json.loads((d/'init-desktop-services.cfg').read_text())
extra['services'].append(dict(name='sheng_display_wake',path=['/compat/bin/native_display_wake'],
 uid='shell',gid=['shell'],apl='system_core',permission=['ohos.permission.POWER_MANAGER'],
 disabled=1,once=1,sandbox=0,**{'start-mode':'condition'}))
extra['jobs'].append(dict(name='param:sheng-display-wake',condition='sheng.debug.display.wake=true',
 cmds=['mkdir /data/local/tmp/sheng-capture 0755 shell shell','start sheng_display_wake']))
(d/'init-desktop-services.cfg').write_text(json.dumps(extra,indent=2)+'\n')
shutil.copy2(r/'tools/configs/init-core-v71.cfg',r/'tools/configs/init-core-v72.cfg')
p=r/'tools/probe_graphics.inc';s=p.read_text();marker='    if(graphics_run_script("/graphics/apply-app-sandbox.sh")<0)return -1;'
assert s.count(marker)==1
s=s.replace(marker,marker+'\n    if(copy_ram_asset("/graphics/native_display_wake","/hmos-root/compat/bin/native_display_wake",0755)<0)return -1;')
p.write_text(s)
p=r/'tools/hmos_probe.c';p.write_text(p.read_text().replace('v71','v72'))
for name in ['build_probe','verify']:
 s=(r/f'tools/{name}_v71.py').read_text().replace('v71','v72')
 if name=='verify':s=s.replace("'sheng_swipe_probe'}","'sheng_swipe_probe','sheng_display_wake'}")
 (r/f'tools/{name}_v72.py').write_text(s)
print('v72 staged: dynamic ptrace child lifecycle; independent native DMS wake; small read-only scanout')
