"""Start donor AVCodec and restore foundation's real phone-state registry."""
from pathlib import Path
import json
import shutil

r=Path(__file__).resolve().parent.parent
d=r/'compat/sheng-graphics/v104'
assert not d.exists()
shutil.copytree(r/'compat/sheng-graphics/v103',d)
for p in list(d.iterdir()):
    if p.is_file() and p.suffix in {'.cfg','.sh'}:
        q=p.with_name(p.name.replace('v103','v104'))
        data=p.read_text(encoding='utf-8').replace('v103','v104')
        if q!=p:p.unlink()
        q.write_text(data,encoding='utf-8',newline='\n')
for name in ['hmos_probe_v103.c','probe_graphics_v103.inc','probe_command_v103.inc',
             'build_probe_v103.py','verify_v103.py','start_native_desktop_v103.sh']:
    (r/'tools'/name.replace('v103','v104')).write_text(
        (r/'tools'/name).read_text(encoding='utf-8').replace('v103','v104'),newline='\n')
for name in ['init-core-v103.cfg','sheng-graphics-v103.hcs']:
    src=r/'tools/configs'/name
    if src.suffix=='.cfg':
        (src.with_name(name.replace('v103','v104'))).write_text(src.read_text().replace('v103','v104'),newline='\n')
    else:shutil.copy2(src,src.with_name(name.replace('v103','v104')))

base=r/'work/hmos_system/system/system'
cfg=json.loads((d/'init-platform-v104.cfg').read_text())
service=json.loads((base/'etc/init/process.cfg').read_text())['services'][0]
assert service['name']=='av_codec_service'
service.update(disabled=1,once=1,sandbox=0,saspawn=False)
service['start-mode']='condition'
cfg['services'].append(service)
cfg['jobs'].append(dict(name='param:sheng-codec',condition='sheng.debug.start.codec=true',cmds=['start av_codec_service']))
(d/'init-platform-v104.cfg').write_text(json.dumps(cfg,indent=2)+'\n',newline='\n')

orig=json.loads((base/'profile/foundation.json').read_text())
registry=next(x for x in orig['systemability'] if x['name']==4009)
p=d/'foundation-app-core.json'
profile=json.loads(p.read_text())
assert all(x['name']!=4009 for x in profile['systemability'])
profile['systemability'].append(registry)
p.write_text(json.dumps(profile,indent=2)+'\n',newline='\n')

p=d/'start-native-desktop-v104.sh'
s=p.read_text()
marker='echo AUTOSTART_ORIGINAL_MEDIA_SA3002_READY\n'
assert s.count(marker)==1
s=s.replace(marker,marker+'''stage=codec
$B chroot "$R" /system/bin/param set sheng.debug.start.codec true
deadline=$(($(now)+20))
while ! $B timeout 3 $B chroot "$R" /compat/bin/native_sa_check 3011; do
 if [ "$(now)" -ge "$deadline" ]; then echo AVCODEC_NOT_READY=1; break; fi
 $B sleep 1
done
''')
p.write_text(s,newline='\n')
(r/'tools/start_native_desktop_v104.sh').write_text(s,newline='\n')
p=r/'tools/verify_v104.py'
s=p.read_text().replace("'pasteboard_service','msdp','faultloggerd'}", "'pasteboard_service','msdp','faultloggerd','av_codec_service'}")
s=s.replace("'msdp_musl.cfg','faultloggerd.cfg']:","'msdp_musl.cfg','faultloggerd.cfg','process.cfg']:")
marker=" assert b'start-wifi-v104.sh' in binary"
assert s.count(marker)==1
s=s.replace(marker,''' foundation=json.loads(new['graphics/foundation-app-core.json'][1])
 registry=next(x for x in foundation['systemability'] if x['name']==4009)
 assert registry==next(x for x in json.loads((root/'work/hmos_system/system/system/profile/foundation.json').read_text())['systemability'] if x['name']==4009)
 assert b'sheng.debug.start.codec true' in new['graphics/start-native-desktop-v104.sh'][1]
'''+marker)
p.write_text(s,newline='\n')
print('v104 prepared: real AVCodec3011 and foundation phone-state registry4009')
