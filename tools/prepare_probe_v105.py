"""Restore the donor time SA with its original identity and clock capabilities."""
from pathlib import Path
import json
import shutil

r=Path(__file__).resolve().parent.parent
d=r/'compat/sheng-graphics/v105'
assert not d.exists()
shutil.copytree(r/'compat/sheng-graphics/v104',d)
for p in list(d.iterdir()):
    if p.is_file() and p.suffix in {'.cfg','.sh'}:
        q=p.with_name(p.name.replace('v104','v105'))
        data=p.read_text(encoding='utf-8').replace('v104','v105')
        if q!=p:p.unlink()
        q.write_text(data,encoding='utf-8',newline='\n')
for name in ['hmos_probe_v104.c','probe_graphics_v104.inc','probe_command_v104.inc',
             'build_probe_v104.py','verify_v104.py','start_native_desktop_v104.sh']:
    (r/'tools'/name.replace('v104','v105')).write_text(
        (r/'tools'/name).read_text(encoding='utf-8').replace('v104','v105'),newline='\n')
for name in ['init-core-v104.cfg','sheng-graphics-v104.hcs']:
    src=r/'tools/configs'/name
    if src.suffix=='.cfg':
        src.with_name(name.replace('v104','v105')).write_text(src.read_text().replace('v104','v105'),newline='\n')
    else:shutil.copy2(src,src.with_name(name.replace('v104','v105')))

base=r/'work/hmos_system/system/system'
original=json.loads((base/'etc/init/timeservice.cfg').read_text())
service=original['services'][0]
assert service['name']=='time_service' and service['caps']==['SYS_TIME','WAKE_ALARM']
service.update(disabled=1,once=1,sandbox=0,saspawn=False)
service['start-mode']='condition'
p=d/'init-platform-v105.cfg'
cfg=json.loads(p.read_text())
cfg['services'].append(service)
cmds=original['jobs'][0]['cmds']
assert cmds[-1]=='start time_service'
cfg['jobs'].append(dict(name='param:sheng-time',condition='sheng.debug.start.time=true',cmds=cmds))
p.write_text(json.dumps(cfg,indent=2)+'\n',newline='\n')

p=d/'start-native-desktop-v105.sh'
s=p.read_text()
marker='echo AUTOSTART_DATABASE_READY\n'
assert s.count(marker)==1
s=s.replace(marker,marker+'''stage=time
$B chroot "$R" /system/bin/param set sheng.debug.start.time true
deadline=$(($(now)+15))
while ! $B timeout 3 $B chroot "$R" /compat/bin/native_sa_check 3702; do
 if [ "$(now)" -ge "$deadline" ]; then echo TIME_SERVICE_NOT_READY=1; break; fi
 $B sleep 1
done
''')
p.write_text(s,newline='\n')
(r/'tools/start_native_desktop_v105.sh').write_text(s,newline='\n')
p=r/'tools/verify_v105.py'
s=p.read_text().replace("'faultloggerd','av_codec_service'}","'faultloggerd','av_codec_service','time_service'}")
s=s.replace("'faultloggerd.cfg','process.cfg']:","'faultloggerd.cfg','process.cfg','timeservice.cfg']:")
s=s.replace("'permission_acls','secon','socket']:","'permission_acls','secon','socket','caps']:")
marker=" assert b'start-wifi-v105.sh' in binary"
assert s.count(marker)==1
s=s.replace(marker," assert b'sheng.debug.start.time true' in new['graphics/start-native-desktop-v105.sh'][1]\n"+marker)
p.write_text(s,newline='\n')
print('v105 prepared: donor time_service3702, original SYS_TIME/WAKE_ALARM; no clock or settings faked')
