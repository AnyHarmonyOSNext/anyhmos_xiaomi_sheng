"""Expose the original missing DeviceInfo/DM providers with original identities."""
from pathlib import Path
import copy
import json
import shutil
r=Path(__file__).resolve().parent.parent
d=r/'compat/sheng-graphics/v115';assert not d.exists()
shutil.copytree(r/'compat/sheng-graphics/v114',d)
for p in list(d.iterdir()):
    if p.is_file() and p.suffix in {'.cfg','.sh'}:
        q=p.with_name(p.name.replace('v114','v115'))
        s=p.read_text(encoding='utf-8').replace('v114','v115')
        if p!=q:p.unlink()
        q.write_text(s,encoding='utf-8',newline='\n')
for name in ['hmos_probe_v114.c','probe_graphics_v114.inc','probe_command_v114.inc',
             'build_probe_v114.py','verify_v114.py','start_native_desktop_v114.sh']:
    (r/'tools'/name.replace('v114','v115')).write_text(
        (r/'tools'/name).read_text(encoding='utf-8').replace('v114','v115'),encoding='utf-8',newline='\n')
for name in ['init-core-v114.cfg','sheng-graphics-v114.hcs']:
    p=r/'tools/configs'/name;q=p.with_name(name.replace('v114','v115'))
    if p.suffix=='.cfg':q.write_text(p.read_text(encoding='utf-8').replace('v114','v115'),encoding='utf-8',newline='\n')
    else:shutil.copy2(p,q)
base=r/'work/hmos_system/system/system'
p=d/'init-platform-v115.cfg';cfg=json.loads(p.read_text(encoding='utf-8'))
for name in ['deviceinfoservice','device_manager']:
    orig=json.loads((base/'etc/init'/f'{name}.cfg').read_text(encoding='utf-8'))
    svc=copy.deepcopy(orig['services'][0])
    for field in ['ondemand','start-on-demand']:svc.pop(field,None)
    svc.update(disabled=1,once=1,sandbox=0,saspawn=False)
    svc['start-mode']='condition'
    cfg['services'].append(svc)
    cfg['jobs']+=orig.get('jobs',[])
    # Keep the donor profile byte-for-byte, including permissions/real methods.
    shutil.copy2(base/'profile'/f'{name}.json',d/f'{name}.json')
cfg['jobs'].append(dict(name='param:sheng-original-device-providers',
    condition='sheng.debug.start.deviceproviders=true',cmds=['start deviceinfoservice','start device_manager']))
p.write_text(json.dumps(cfg,indent=2)+'\n',encoding='utf-8',newline='\n')
p=r/'tools/probe_graphics_v115.inc';s=p.read_text(encoding='utf-8')
old='"i18n_service.json","service_router.json","download_server.json"'
assert s.count(old)==1
s=s.replace(old,old+',"deviceinfoservice.json","device_manager.json"')
p.write_text(s,encoding='utf-8',newline='\n')
for p in [d/'start-native-desktop-v115.sh',r/'tools/start_native_desktop_v115.sh']:
    s=p.read_text(encoding='utf-8');marker='stage=database\n';assert s.count(marker)==1
    s=s.replace(marker,'stage=deviceproviders\n$B chroot "$R" /system/bin/param set sheng.debug.start.deviceproviders true\nstage=database\n')
    p.write_text(s,encoding='utf-8',newline='\n')
p=r/'tools/verify_v115.py';s=p.read_text(encoding='utf-8')
s=s.replace("'service_router','download_server'}","'service_router','download_server','deviceinfoservice','device_manager'}")
s=s.replace("'srms.cfg','downloadservice.cfg']:","'srms.cfg','downloadservice.cfg','deviceinfoservice.cfg','device_manager.cfg']:")
marker=" assert b'start-wifi-v115.sh' in binary";assert s.count(marker)==1
s=s.replace(marker," for profile in ['deviceinfoservice.json','device_manager.json']:\n  assert new['graphics/'+profile][1]==(root/'work/hmos_system/system/system/profile'/profile).read_bytes()\n assert b'sheng.debug.start.deviceproviders true' in new['graphics/start-native-desktop-v115.sh'][1]\n"+marker)
p.write_text(s,encoding='utf-8',newline='\n')
print('v115 prepared: donor DeviceInfo3902 and DM4802, original uid/gid/token permissions, no hardware or audio autostart')
