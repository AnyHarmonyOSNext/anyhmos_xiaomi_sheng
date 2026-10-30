"""Freeze v82; stage the first hardware-services round without touching vendor."""
from pathlib import Path
import shutil,json
r=Path(__file__).resolve().parent.parent
out=r/'compat/sheng-graphics/v83'
if out.exists():raise SystemExit('v83 already exists; edit its sources explicitly')
shutil.copytree(r/'compat/sheng-graphics/v82',out)
for name in ['hmos_probe_v82.c','probe_graphics_v82.inc','probe_command_v82.inc','build_probe_v82.py','verify_v82.py','start_native_desktop_v82.sh']:
 p=r/'tools'/name;dest=p.with_name(name.replace('v82','v83'));assert not dest.exists()
 dest.write_text(p.read_text(encoding='utf-8').replace('v82','v83'),encoding='utf-8',newline='\n')
cfg=r/'tools/configs/init-core-v83.cfg'
core=json.loads((r/'tools/configs/init-core-v82.cfg').read_text(encoding='utf-8'))
core['import'].append('/compat/etc/init-hardware-v83.cfg')
cfg.write_text(json.dumps(core,indent=2)+'\n',encoding='utf-8')
for old,new in [('apply-runtime-v82.sh','apply-runtime-v83.sh'),('start-native-desktop-v82.sh','start-native-desktop-v83.sh'),('start-graphics-v82.sh','start-graphics-v83.sh')]:
 p=out/old;dest=out/new
 dest.write_text(p.read_text(encoding='utf-8').replace('v82','v83'),encoding='utf-8',newline='\n');p.unlink()
shutil.copy2(r/'compat/sheng-graphics/hardware-display-v1/libdisplay_composer_vdi_impl.z.so',out/'libdisplay_composer_vdi_impl.z.so')
for name in ['sheng_hardware_display','hardware_observe']:shutil.copy2(r/'compat/debug-tools'/name,out/name)
# Native service identity/permissions are taken from the actual donor configs.
stock=r/'work/hmos_system/system/system'
hardware={'jobs':[{'name':'sheng-hardware','condition':'sheng.debug.start.hardware=true','cmds':['start powermgr','start deviceinfoservice','start media_service']}],'services':[]}
for name in ['powermgr','deviceinfoservice','media_service']:
 svc=json.loads((stock/f'etc/init/{name}.cfg').read_text(encoding='utf-8'))['services'][0]
 for k in ['critical','jobs','ondemand','writepid','bootevents']:svc.pop(k,None)
 svc.update(disabled=1,once=1,sandbox=0,saspawn=False)
 svc['start-mode']='condition'
 if name=='powermgr':svc['path']=['/system/bin/sa_main','/compat/etc/displaymgr-profile.json']
 hardware['services'].append(svc)
(out/'init-hardware-v83.cfg').write_text(json.dumps(hardware,indent=2)+'\n',encoding='utf-8')
profile=json.loads((stock/'profile/powermgr.json').read_text(encoding='utf-8'))
# Start display policy alone first; suspend/thermal/battery need matching native HDIs.
profile['systemability']=[s for s in profile['systemability'] if s['name']==3308]
(out/'displaymgr-profile.json').write_text(json.dumps(profile,indent=2)+'\n',encoding='utf-8')
(out/'apply-hardware-v83.sh').write_text('''#!/bin/sh
set -eu
B=/busybox
R=/hmos-root
$B mkdir -p $R/compat/etc $R/compat/bin
for name in init-hardware-v83.cfg displaymgr-profile.json; do
 $B cp /graphics/$name $R/compat/etc/$name
 $B chmod 0644 $R/compat/etc/$name
done
for name in sheng_hardware_display hardware_observe; do
 $B cp /graphics/$name $R/compat/bin/$name
 $B chmod 0755 $R/compat/bin/$name
done
# Only the actual composer host group receives hardware backlight write access.
$B chown 0:3036 /sys/class/backlight/panel0-backlight/brightness
$B chmod 0660 /sys/class/backlight/panel0-backlight/brightness
$B mkdir -p $R/data/service/el0/stats $R/data/service/el0/thermal/config
$B chown -R 5528:5528 $R/data/service/el0/stats $R/data/service/el0/thermal
echo SHENG_V83_DISPLAY_AND_HARDWARE_SERVICES_STAGED_VENDOR_UNTOUCHED
''',encoding='utf-8',newline='\n')
p=out/'apply-runtime-v83.sh'
p.write_text(p.read_text(encoding='utf-8')+'\n$B sh /graphics/apply-hardware-v83.sh\n',encoding='utf-8',newline='\n')
for p in [out/'start-native-desktop-v83.sh',r/'tools/start_native_desktop_v83.sh']:
 s=p.read_text(encoding='utf-8');needle='stage=capture\n';assert s.count(needle)==1
 s=s.replace(needle,'stage=hardware\n$B chroot "$R" /system/bin/param set sheng.debug.start.hardware true\n'+needle)
 p.write_text(s,encoding='utf-8',newline='\n')
p=r/'tools/verify_v83.py';s=p.read_text(encoding='utf-8')
s=s.replace('compat/sheng-graphics/panel-capability-v1/libdisplay_composer_vdi_impl.z.so','compat/sheng-graphics/hardware-display-v1/libdisplay_composer_vdi_impl.z.so')
s=s.replace("assert config['import']==['/compat/etc/init-desktop-services.cfg']", "assert config['import']==['/compat/etc/init-desktop-services.cfg','/compat/etc/init-hardware-v83.cfg']")
# Retain all v82 exact checks; additionally verify isolated new config/services/assets.
needle=" config=json.loads(new['hmos-init-debug.cfg'][1]);"
assert needle in s
s=s.replace(needle," hardware=json.loads(new['graphics/init-hardware-v83.cfg'][1]);assert {x['name'] for x in hardware['services']}=={'powermgr','deviceinfoservice','media_service'};assert all(x['once']==1 and 'critical' not in x for x in hardware['services'])\n assert [x['name'] for x in json.loads(new['graphics/displaymgr-profile.json'][1])['systemability']]==[3308]\n"+needle)
p.write_text(s,encoding='utf-8',newline='\n')
print('v83 staged; build and full unpack verification still required')
