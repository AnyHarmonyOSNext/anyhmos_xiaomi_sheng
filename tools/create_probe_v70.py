"""Freeze v69 and stage original MMI with gated startup and privacy SDK fix."""
from pathlib import Path
import hashlib
import json
import shutil

r = Path(__file__).resolve().parent.parent
for name in ['hmos_probe.c', 'probe_graphics.inc', 'probe_command.inc']:
    p = r / 'tools' / name
    frozen = r / 'tools/archive' / (p.stem + '_v69' + p.suffix)
    if not frozen.exists():
        shutil.copy2(p, frozen)
d = r / 'compat/sheng-graphics/v70'
assert not d.exists()
shutil.copytree(r / 'compat/sheng-graphics/v69', d)
lib = r / 'work/privacy-nonblocking.so'
assert hashlib.sha256(lib.read_bytes()).hexdigest() == 'b193f5ab4919893a90d28ada02c000fccefeb16548f81315175f69802d5af9de'
shutil.copy2(lib, d / 'libsps_privacy_indicator_service_intf.z.so')
shutil.copy2(r / 'compat/debug-tools/native_sa_dump', d / 'native_sa_dump')
core = json.loads((r / 'tools/configs/init-core-v69.cfg').read_text())
job = next(j for j in core['jobs'] if j['name'] == 'sheng-screen-data')
job['cmds'].append('mkdir /data/service/el1/public/screenlock 0755 foundation foundation')
(r / 'tools/configs/init-core-v70.cfg').write_text(json.dumps(core, indent=2)+'\n')
extra = json.loads((d / 'init-desktop-services.cfg').read_text())
original = json.loads((r / 'work/hmos_system/system/system/etc/init/multimodalinput.cfg').read_text())
service = original['services'][0]
for key in ['critical', 'writepid']:
    service.pop(key, None)
service.update(disabled=1, once=1, sandbox=0, saspawn=False)
extra['services'].append(service)
extra['jobs'].append(dict(name='param:sheng-debug-input', condition='sheng.debug.start.input=true', cmds=[
    'mkdir /dev/char 0755 root system',
    'mkdir /dev/v4l 0755 root system',
    'mkdir /data/service/el1/public/udev 0711 root system',
    'mkdir /data/service/el1/public/multimodalinput 0744 input input',
    'start multimodalinput']))
(d / 'init-desktop-services.cfg').write_text(json.dumps(extra, indent=2)+'\n')
p = r / 'tools/probe_graphics.inc'
s = p.read_text()
marker = '    note("SYSTEM_OPTIONAL_SDK_COMPAT_BIND: nonblocking hotspot SA1154 and sensor SA3601; vendor untouched");'
assert s.count(marker) == 1
s = s.replace(marker, marker + '''
    if(copy_ram_asset("/graphics/libsps_privacy_indicator_service_intf.z.so","/hmos-root/compat/lib64/libsps_privacy_indicator_service_intf.z.so",0644)<0)return -1;
    if(mount("/hmos-root/compat/lib64/libsps_privacy_indicator_service_intf.z.so","/hmos-root/system/lib64/libsps_privacy_indicator_service_intf.z.so",NULL,MS_BIND,NULL)<0)return -1;
    if(copy_ram_asset("/graphics/native_sa_dump","/hmos-root/data/local/tmp/native_sa_dump",0755)<0)return -1;
    note("SYSTEM_PRIVACY_SDK_COMPAT_BIND: original nonblocking SA66090 query; vendor untouched");''')
marker = '    note("HMOS two-host graphics trial staged in RAM; vendor mounted read-only; private hardware libraries in /compat");return 0;'
assert s.count(marker) == 1
s = s.replace(marker, '''    if(mkdirs("/hmos-root/dev/input")<0||chmod("/hmos-root/dev/input",0755)<0)return -1;
    DIR *inputs=opendir("/sys/class/input");
    if(inputs){struct dirent *input;
        while((input=readdir(inputs))){
            if(strncmp(input->d_name,"event",5)||!input->d_name[5])continue;
            const char *digit=input->d_name+5;while(*digit>='0'&&*digit<='9')digit++;
            if(*digit)continue;
            char sys[512],target[512];
            snprintf(sys,sizeof(sys),"/sys/class/input/%s",input->d_name);
            snprintf(target,sizeof(target),"/hmos-root/dev/input/%s",input->d_name);
            if(node_from_sys(sys,target,S_IFCHR)<0||chown(target,6696,6696)<0||chmod(target,0660)<0){closedir(inputs);return -1;}
            note("HMOS_INPUT_NODE: %s from real sysfs; uid/gid input",target);
        }
        closedir(inputs);
    }
''' + marker)
p.write_text(s)
p = r / 'tools/hmos_probe.c'
p.write_text(p.read_text().replace('v69', 'v70'))
for name in ['build_probe', 'verify']:
    s = (r / f'tools/{name}_v69.py').read_text().replace('v69', 'v70')
    if name == 'verify':
        s = s.replace("'ui_service','locationhub'}", "'ui_service','locationhub','multimodalinput'}")
        marker = " assert config['import']==['/compat/etc/init-desktop-services.cfg']"
        assert s.count(marker) == 1
        s = s.replace(marker, " assert hashlib.sha256(new['graphics/libsps_privacy_indicator_service_intf.z.so'][1]).hexdigest()=='b193f5ab4919893a90d28ada02c000fccefeb16548f81315175f69802d5af9de'\n"+marker)
    (r / f'tools/{name}_v70.py').write_text(s)
print('v70 staged: privacy fix, original MMI gate, real evdev nodes, screenlock directory')
