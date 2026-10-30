"""Add the donor input-method and network services; start WLAN before UI clients."""
from pathlib import Path
import json
import shutil

r = Path(__file__).resolve().parent.parent
d = r/'compat/sheng-graphics/v102'
assert not d.exists()
shutil.copytree(r/'compat/sheng-graphics/v101', d)
for p in list(d.iterdir()):
    if p.is_file() and p.suffix in {'.sh', '.cfg'}:
        q = p.with_name(p.name.replace('v101', 'v102'))
        content = p.read_text(encoding='utf-8').replace('v101', 'v102').replace('V101', 'V102')
        if p != q:
            p.unlink()
        q.write_text(content, encoding='utf-8', newline='\n')
for name in ['hmos_probe_v101.c', 'probe_graphics_v101.inc', 'probe_command_v101.inc',
             'build_probe_v101.py', 'verify_v101.py', 'start_native_desktop_v101.sh']:
    (r/'tools'/name.replace('v101', 'v102')).write_text(
        (r/'tools'/name).read_text(encoding='utf-8').replace('v101', 'v102'),
        encoding='utf-8', newline='\n')
shutil.copy2(r/'tools/configs/sheng-graphics-v101.hcs', r/'tools/configs/sheng-graphics-v102.hcs')

core = json.loads((r/'tools/configs/init-core-v101.cfg').read_text().replace('v101', 'v102'))
core['import'].append('/compat/etc/init-platform-v102.cfg')
(r/'tools/configs/init-core-v102.cfg').write_text(json.dumps(core, indent=2)+'\n', newline='\n')

base = r/'work/hmos_system/system/system/etc/init'
services = []
for filename in ['inputmethodservice.cfg', 'netsysnative.cfg', 'netmanager_base.cfg']:
    original = json.loads((base/filename).read_text())['services'][0]
    # Original UID, groups, SELinux domain, sockets and token permission lists.
    for key in ['critical', 'bootevents', 'ondemand']:
        original.pop(key, None)
    original.update(disabled=1, once=1, sandbox=0, saspawn=False)
    original['start-mode'] = 'condition'
    if original['name'] == 'inputmethod_service':
        original['jobs'] = {'on-start': 'services:sheng-ime'}
    services.append(original)

jobs = [
    dict(name='services:sheng-ime', cmds=[
        'mkdir /data/service/el1/public/imf 0711 inputmethod inputmethod']),
    dict(name='services:netsysnative', cmds=[
        'mkdir /data/service/el1/public/netsysnative 0711 netsysnative netsysnative',
        'mount bpf bpf /sys/fs/bpf nodev',
        'mount cgroup2 none /sys/fs/cgroup nodev']),
    dict(name='services:netmanager', cmds=[
        'mkdir /data/service/el1/public/netmanager 0711 net_manager net_manager',
        'mkdir /data/service/el1/public/netmanager/route 0711 net_manager net_manager',
        'mkdir /data/service/el1/public/hosts_user 0755 root root']),
    dict(name='param:sheng-platform-ime', condition='sheng.debug.start.ime=true',
         cmds=['start inputmethod_service']),
    dict(name='param:sheng-platform-netstack', condition='sheng.debug.start.netstack=true',
         cmds=['start netsysnative', 'start netmanager']),
]
(d/'init-platform-v102.cfg').write_text(json.dumps(dict(jobs=jobs, services=services), indent=2)+'\n', newline='\n')
p = r/'tools/probe_graphics_v102.inc'
s = p.read_text()
marker = 'const char *wifi_assets[]={"init-wifi-v102.cfg",'
assert s.count(marker) == 1
s = s.replace(marker, 'const char *wifi_assets[]={"init-platform-v102.cfg","init-wifi-v102.cfg",')
p.write_text(s, newline='\n')

p = d/'start-native-desktop-v102.sh'
s = p.read_text()
marker = 'stage=graphics\n'
assert s.count(marker) == 1
s = s.replace(marker, '''# Initialize the real WLAN hosts before UI code can request WiFi SAs.
stage=wireless
if $B timeout 50 $B sh "$R/compat/bin/start-wifi-v102.sh" > "$R/data/local/tmp/v102-wifi-startup.log" 2>&1; then
 echo AUTOSTART_WLAN_REQUESTED=1
else
 echo AUTOSTART_WLAN_REQUEST_FAILED=1
fi
stage=netstack
$B chroot "$R" /system/bin/param set sheng.debug.start.netstack true
for id in 1120 1124 1126 1158 1151; do
 deadline=$(($(now)+15))
 while ! $B timeout 3 $B chroot "$R" /compat/bin/native_sa_check "$id"; do
  if [ "$(now)" -ge "$deadline" ]; then echo "PLATFORM_SA_NOT_READY=$id"; break; fi
  $B sleep 1
 done
done
'''+marker)
marker = '$B chroot "$R" /system/bin/param set sheng.debug.start.compconfig true\n'
assert s.count(marker) == 1
s = s.replace(marker, marker+'''stage=inputmethod
$B chroot "$R" /system/bin/param set sheng.debug.start.ime true
deadline=$(($(now)+25))
while ! $B timeout 3 $B chroot "$R" /compat/bin/native_sa_check 3703; do
 if [ "$(now)" -ge "$deadline" ]; then echo INPUTMETHOD_NOT_READY=1; break; fi
 $B sleep 1
done
stage=scene
''')
p.write_text(s, newline='\n')
# Keep the parallel archival shell source consistent with the packaged asset.
(r/'tools/start_native_desktop_v102.sh').write_text(s, newline='\n')
p = r/'tools/build_probe_v102.py'
s = p.read_text().replace("root/'tools/configs/sheng-graphics.hcs'", "root/'tools/configs/sheng-graphics-v102.hcs'")
p.write_text(s, newline='\n')
p = r/'tools/verify_v102.py'
s = p.read_text()
marker = "'/compat/etc/init-wifi-v102.cfg']"
assert s.count(marker) == 1
s = s.replace(marker, "'/compat/etc/init-wifi-v102.cfg','/compat/etc/init-platform-v102.cfg']")
marker = " assert b'start-wifi-v102.sh' in binary"
assert s.count(marker) == 1
s = s.replace(marker, ''' platform=json.loads(new['graphics/init-platform-v102.cfg'][1])
 assert {x['name'] for x in platform['services']}=={'inputmethod_service','netsysnative','netmanager'}
 assert all(x['once']==1 and 'critical' not in x for x in platform['services'])
 for filename in ['inputmethodservice.cfg','netsysnative.cfg','netmanager_base.cfg']:
  original=json.loads((root/'work/hmos_system/system/system/etc/init'/filename).read_text())['services'][0]
  service=next(x for x in platform['services'] if x['name']==original['name'])
  for k in ['path','uid','gid','permission','permission_acls','secon','socket']:
   if k in original:assert service[k]==original[k],(original['name'],k)
 assert b'AUTOSTART_WLAN_REQUESTED' in new['graphics/start-native-desktop-v102.sh'][1]
 assert b'sheng.debug.start.ime true' in new['graphics/start-native-desktop-v102.sh'][1]
'''+marker)
p.write_text(s, newline='\n')
print('v102 prepared: original IMSA + network stack; WLAN initialization precedes desktop')
