"""Restore real clipboard and drag services before apps request input panels."""
from pathlib import Path
import copy
import json
import shutil

r = Path(__file__).resolve().parent.parent
d = r / 'compat/sheng-graphics/v103'
assert not d.exists()
shutil.copytree(r / 'compat/sheng-graphics/v102', d)
for p in list(d.iterdir()):
    if p.is_file() and p.suffix in {'.sh', '.cfg'}:
        q = p.with_name(p.name.replace('v102', 'v103'))
        data = p.read_text(encoding='utf-8').replace('v102', 'v103')
        if p != q:
            p.unlink()
        q.write_text(data, encoding='utf-8', newline='\n')
for name in ['hmos_probe_v102.c', 'probe_graphics_v102.inc', 'probe_command_v102.inc',
             'build_probe_v102.py', 'verify_v102.py', 'start_native_desktop_v102.sh']:
    (r/'tools'/name.replace('v102','v103')).write_text(
        (r/'tools'/name).read_text(encoding='utf-8').replace('v102','v103'),
        encoding='utf-8', newline='\n')
shutil.copy2(r/'tools/configs/sheng-graphics-v102.hcs', r/'tools/configs/sheng-graphics-v103.hcs')
shutil.copy2(r/'tools/configs/init-core-v102.cfg', r/'tools/configs/init-core-v103.cfg')
p = r/'tools/configs/init-core-v103.cfg'
p.write_text(p.read_text().replace('v102','v103'), encoding='utf-8', newline='\n')

base = r/'work/hmos_system/system/system'
platform = json.loads((d/'init-platform-v103.cfg').read_text())
for filename in ['pasteboardservice.cfg', 'msdp_musl.cfg', 'faultloggerd.cfg']:
    original = json.loads((base/'etc/init'/filename).read_text())
    service = copy.deepcopy(original['services'][0])
    for key in ['critical','bootevents','ondemand','writepid']:
        service.pop(key,None)
    service.update(disabled=1,once=1,sandbox=0,saspawn=False)
    service['start-mode']='condition'
    if service['name']=='msdp':
        service['jobs']={'on-start':'services:sheng-msdp-input'}
    platform['services'].append(service)
    if service['name']=='faultloggerd':
        job=next(x for x in original['jobs'] if x['name']=='services:faultloggerd')
        # Snapdragon has none of these donor-only hardware debug devices.
        job['cmds']=[x for x in job['cmds'] if '/sys/kbox/' not in x and '/dev/pdump' not in x and '/dev/lperf' not in x]
        platform['jobs'].append(job)
platform['jobs'].extend([
    dict(name='services:sheng-msdp-input',cmds=[
        'mkdir /data/service/el1/public/msdp 0755 msdp msdp',
        'mkdir /data/service/el2/public/msdp 0755 msdp msdp']),
    dict(name='param:sheng-platform-diagnostics',condition='sheng.debug.start.diagnostics=true',cmds=[
        'mkdir /data/log/eventlog 0771 system log',
        'mkdir /data/log/eventlog/freeze 0770 system system',
        'mkdir /data/log/faultlog 0750 hiview log',
        'mkdir /data/log/faultlog/faultlogger 0750 hiview log',
        'start faultloggerd']),
    dict(name='param:sheng-platform-uideps',condition='sheng.debug.start.uideps=true',cmds=[
        'start pasteboard_service','start msdp'])
])
(d/'init-platform-v103.cfg').write_text(json.dumps(platform,indent=2)+'\n',newline='\n')

clipboard=json.loads((base/'profile/pasteboard_service.json').read_text())
assert len(clipboard['systemability'])==1
clipboard['systemability'][0]['run-on-create']=True
(d/'pasteboard-service-eager.json').write_text(json.dumps(clipboard,indent=2)+'\n',newline='\n')
msdp=json.loads((base/'profile/msdp.json').read_text())
msdp['systemability']=[x for x in msdp['systemability'] if x['name']==2902]
assert len(msdp['systemability'])==1 and msdp['systemability'][0]['run-on-create']
(d/'msdp-input-only.json').write_text(json.dumps(msdp,indent=2)+'\n',newline='\n')

p=r/'tools/probe_graphics_v103.inc'
s=p.read_text()
marker='    const char *wifi_assets[]='
assert s.count(marker)==1
s=s.replace(marker,'''    if(copy_ram_asset("/graphics/pasteboard-service-eager.json","/hmos-root/system/profile/pasteboard_service.json",0644)<0||
       copy_ram_asset("/graphics/msdp-input-only.json","/hmos-root/system/profile/msdp.json",0644)<0)return -1;
'''+marker)
s=s.replace('absent device proxy returns false','real WiFi proxy with nonblocking missing-SA lookup')
p.write_text(s,newline='\n')

p=d/'start-native-desktop-v103.sh'
s=p.read_text()
s=s.replace('stage=database\n', '''stage=diagnostics
$B chroot "$R" /system/bin/param set sheng.debug.start.diagnostics true
stage=database
''')
marker='stage=scene\n$B cp'
assert s.count(marker)==1
s=s.replace(marker,'''stage=uideps
$B chroot "$R" /system/bin/param set sheng.debug.start.uideps true
for id in 3701 2902; do
 deadline=$(($(now)+20))
 while ! $B timeout 3 $B chroot "$R" /compat/bin/native_sa_check "$id"; do
  if [ "$(now)" -ge "$deadline" ]; then echo "UI_DEPENDENCY_NOT_READY=$id"; break; fi
  $B sleep 1
 done
done
'''+marker)
p.write_text(s,newline='\n')
(r/'tools/start_native_desktop_v103.sh').write_text(s,newline='\n')

p=r/'tools/verify_v103.py'
s=p.read_text().replace("{'inputmethod_service','netsysnative','netmanager'}", "{'inputmethod_service','netsysnative','netmanager','pasteboard_service','msdp','faultloggerd'}")
s=s.replace("['inputmethodservice.cfg','netsysnative.cfg','netmanager_base.cfg']:", "['inputmethodservice.cfg','netsysnative.cfg','netmanager_base.cfg','pasteboardservice.cfg','msdp_musl.cfg','faultloggerd.cfg']:")
marker=" assert b'start-wifi-v103.sh' in binary"
assert s.count(marker)==1
s=s.replace(marker,''' clipboard=json.loads(new['graphics/pasteboard-service-eager.json'][1])
 assert clipboard['systemability'][0]['name']==3701 and clipboard['systemability'][0]['run-on-create']
 original=json.loads((root/'work/hmos_system/system/system/profile/msdp.json').read_text())
 msdp=json.loads(new['graphics/msdp-input-only.json'][1])
 assert msdp['systemability']==[x for x in original['systemability'] if x['name']==2902]
 assert b'sheng.debug.start.uideps true' in new['graphics/start-native-desktop-v103.sh'][1]
 assert b'eventlog/freeze' in new['graphics/init-platform-v103.cfg'][1]
'''+marker)
p.write_text(s,newline='\n')
print('v103 prepared: original clipboard + MSDP input SA + faultlogger; no donor sensor SAs')
