"""Persist the verified missing-/compat app-sandbox correction; add native input probe."""
from pathlib import Path
import json
import shutil
import subprocess
import sys

r=Path(__file__).resolve().parent.parent
for name in ['hmos_probe.c','probe_graphics.inc','probe_command.inc']:
 p=r/'tools'/name;q=r/'tools/archive'/(p.stem+'_v70'+p.suffix)
 if not q.exists():shutil.copy2(p,q)
d=r/'compat/sheng-graphics/v71';assert not d.exists()
shutil.copytree(r/'compat/sheng-graphics/v70',d)
subprocess.run([sys.executable,str(r/'tools/prepare_app_sandbox_compat.py')],check=True)
reports=json.loads((r/'analysis/app-sandbox-compat.json').read_text())
script=['set -e','B=/busybox','R=/hmos-root','$B mkdir -p $R/compat/etc/sandbox']
for report in reports:
 name=report['name'];shutil.copy2(r/'work'/('compat-'+name+'.gz'),d/(name+'.gz'))
 script += [f'echo "{report["input_sha256"]}  $R/system/etc/sandbox/{name}" | $B sha256sum -c -',
            f'$B gzip -dc /graphics/{name}.gz > $R/compat/etc/sandbox/{name}',
            f'echo "{report["output_sha256"]}  $R/compat/etc/sandbox/{name}" | $B sha256sum -c -',
            f'$B chmod 0644 $R/compat/etc/sandbox/{name}',
            f'$B mount --bind $R/compat/etc/sandbox/{name} $R/system/etc/sandbox/{name}']
script.append('echo APP_SANDBOX_COMPAT_MOUNT_CONFIGURED')
(d/'apply-app-sandbox.sh').write_text('\n'.join(script)+'\n',newline='\n')
shutil.copy2(r/'compat/debug-tools/native_image_alloc_probe',d/'native_image_alloc_probe')
core=json.loads((r/'tools/configs/init-core-v70.cfg').read_text())
(r/'tools/configs/init-core-v71.cfg').write_text(json.dumps(core,indent=2)+'\n')
extra=json.loads((d/'init-desktop-services.cfg').read_text())
extra['services'].append(dict(name='sheng_swipe_probe',
 path=['/system/bin/uinput','-T','-m','1500','1850','1500','500','500'],
 uid='shell',gid=['shell'],apl='system_core',permission=['ohos.permission.INJECT_INPUT_EVENT'],
 disabled=1,once=1,sandbox=0,**{'start-mode':'condition'}))
extra['jobs'].append(dict(name='param:sheng-swipe-probe',condition='sheng.debug.input.swipe=true',cmds=['start sheng_swipe_probe']))
(d/'init-desktop-services.cfg').write_text(json.dumps(extra,indent=2)+'\n')
p=r/'tools/probe_graphics.inc';s=p.read_text()
marker='    if(copy_ram_asset("/graphics/native_sa_dump","/hmos-root/data/local/tmp/native_sa_dump",0755)<0)return -1;'
assert s.count(marker)==1
s=s.replace(marker,marker+'\n    if(copy_ram_asset("/graphics/native_image_alloc_probe","/hmos-root/data/local/tmp/native_image_alloc_probe",0755)<0)return -1;\n    if(graphics_run_script("/graphics/apply-app-sandbox.sh")<0)return -1;')
p.write_text(s)
p=r/'tools/hmos_probe.c';p.write_text(p.read_text().replace('v70','v71'))
for name in ['build_probe','verify']:
 s=(r/f'tools/{name}_v70.py').read_text().replace('v70','v71')
 if name=='verify':s=s.replace("'locationhub','multimodalinput'}", "'locationhub','multimodalinput','sheng_swipe_probe'}")
 (r/f'tools/{name}_v71.py').write_text(s)
print('v71 staged: app sandbox /compat, original native input-probe token and permissions')
