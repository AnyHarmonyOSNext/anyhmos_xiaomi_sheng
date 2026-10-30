"""Stage aligned allocator and donor compatibility-config SA using its native identity."""
from pathlib import Path
import shutil,json
r=Path(__file__).resolve().parents[1]
d=r/'compat/sheng-graphics/v76'
assert not d.exists()
for name in ['hmos_probe.c','probe_graphics.inc','probe_command.inc']:
    p=r/'tools'/name
    frozen=r/'tools/archive'/(p.stem+'_v75'+p.suffix)
    assert not frozen.exists(); shutil.copy2(p,frozen)
shutil.copytree(r/'compat/sheng-graphics/v75',d)
shutil.copy2(r/'compat/sheng-graphics/stride-v1/libdisplay_buffer_vdi_impl.z.so',d)
original=json.loads((r/'work/hmos_system/system/system/etc/init/compatibility_config_center.cfg').read_text())
extra=json.loads((d/'init-desktop-services.cfg').read_text())
service=original['services'][0]
service.update(disabled=1,once=1,sandbox=0,**{'start-mode':'condition'})
extra['services'].append(service)
extra['jobs']+=original['jobs']
extra['jobs'].append(dict(name='param:sheng-compconfig',condition='sheng.debug.start.compconfig=true',
                         cmds=['start compatibility_config_center']))
(d/'init-desktop-services.cfg').write_text(json.dumps(extra,indent=2)+'\n')
script=d/'init-persistent-ext4.sh'
script.write_text(script.read_text()+'''
# Singleton settingsdata can request its EL2 cache while running as user 0.
$B mkdir -p "$R/data/app/el2/0/base/com.ohos.settingsdata/cache"
$B chmod 0711 "$R/data/app/el2/0" "$R/data/app/el2/0/base"
$B chown 20001:20001 "$R/data/app/el2/0/base/com.ohos.settingsdata" "$R/data/app/el2/0/base/com.ohos.settingsdata/cache"
$B chmod 0700 "$R/data/app/el2/0/base/com.ohos.settingsdata" "$R/data/app/el2/0/base/com.ohos.settingsdata/cache"
echo HMOS_SETTINGS_SINGLETON_CACHE_READY
''',newline='\n')
p=r/'tools/hmos_probe.c';s=p.read_text().replace('v75','v76')
old='if(!strncmp(cmd,"cmd ",4)){command_start(cmd+4);return;}'
assert s.count(old)==1
s=s.replace(old,'''if(!strncmp(cmd,"cmd ",4)){
        // An explicit command takes priority over old unsolicited USB replay.
        // Persistent history remains available through the replay command.
        serial_pos=used;command_start(cmd+4);return;
    }''')
p.write_text(s)
shutil.copy2(r/'tools/configs/init-core-v75.cfg',r/'tools/configs/init-core-v76.cfg')
for name in ['build_probe','verify']:
    s=(r/f'tools/{name}_v75.py').read_text().replace('v75','v76')
    if name=='verify':
        s=s.replace("'sheng_userauth_host','sheng_input_dispatch'}", "'sheng_userauth_host','sheng_input_dispatch','compatibility_config_center'}")
        s=s.replace(" assert image.stat().st_size==8388608", " assert image.stat().st_size==8388608\n assert new['graphics/libdisplay_buffer_vdi_impl.z.so'][1]==(root/'compat/sheng-graphics/stride-v1/libdisplay_buffer_vdi_impl.z.so').read_bytes()")
    (r/f'tools/{name}_v76.py').write_text(s)
print('v76 staged: aligned native buffer, original SA8620, singleton cache, command priority')
