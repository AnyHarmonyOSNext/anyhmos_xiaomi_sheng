"""Persist real MemAvailable and restore requested framework service providers."""
from pathlib import Path
import copy
import json
import shutil

r = Path(__file__).resolve().parent.parent
d = r / 'compat/sheng-graphics/v110'
assert not d.exists()
shutil.copytree(r / 'compat/sheng-graphics/v109', d)
for p in list(d.iterdir()):
    if p.is_file() and p.suffix in {'.cfg', '.sh'}:
        q = p.with_name(p.name.replace('v109', 'v110'))
        content = p.read_text(encoding='utf-8').replace('v109', 'v110')
        if q != p: p.unlink()
        q.write_text(content, encoding='utf-8', newline='\n')
for name in ['hmos_probe_v109.c', 'probe_graphics_v109.inc', 'probe_command_v109.inc',
             'build_probe_v109.py', 'verify_v109.py', 'start_native_desktop_v109.sh']:
    (r/'tools'/name.replace('v109', 'v110')).write_text(
        (r/'tools'/name).read_text(encoding='utf-8').replace('v109', 'v110'),
        encoding='utf-8', newline='\n')
for name in ['init-core-v109.cfg', 'sheng-graphics-v109.hcs']:
    p = r/'tools/configs'/name
    q = p.with_name(name.replace('v109', 'v110'))
    if p.suffix == '.cfg': q.write_text(p.read_text(encoding='utf-8').replace('v109', 'v110'), encoding='utf-8', newline='\n')
    else: shutil.copy2(p, q)

(d/'apply-memmgr-v1.sh').unlink()
shutil.copy2(r/'compat/sheng-framework/memmgr-v2/apply-memmgr-v2.sh', d/'apply-memmgr-v2.sh')
p = d/'apply-runtime-v110.sh'
p.write_text(p.read_text(encoding='utf-8').replace('apply-memmgr-v1.sh', 'apply-memmgr-v2.sh'), encoding='utf-8', newline='\n')

base = r/'work/hmos_system/system/system'
p = d/'init-platform-v110.cfg'
platform = json.loads(p.read_text(encoding='utf-8'))
names = []
for cfg in ['i18n_service.cfg', 'srms.cfg', 'downloadservice.cfg']:
    orig = json.loads((base/'etc/init'/cfg).read_text(encoding='utf-8'))
    svc = copy.deepcopy(orig['services'][0])
    names.append(svc['name'])
    svc.update(disabled=1, once=1, sandbox=0, saspawn=False)
    svc['start-mode'] = 'condition'
    platform['services'].append(svc)
    if cfg == 'downloadservice.cfg': platform['jobs'] += orig['jobs']
    profile = Path(svc['path'][1]).name
    c = json.loads((base/'profile'/profile).read_text(encoding='utf-8'))
    assert len(c['systemability']) == 1
    c['systemability'][0]['run-on-create'] = True
    (d/profile).write_text(json.dumps(c, indent=2)+'\n', encoding='utf-8', newline='\n')
cmds = [f'mkdir /data/service/el1/public/i18n{suffix} {mode} i18n i18n'
        for suffix, mode in [('', '0755'), ('/timezone', '0755'), ('/libphonenumber', '0755'),
                             ('/taboo', '0755'), ('/global', '0777'), ('/icu', '0755')]]
cmds += ['start '+name for name in names]
platform['jobs'].append(dict(name='param:sheng-framework-providers',
    condition='sheng.debug.start.framework=true', cmds=cmds))
p.write_text(json.dumps(platform, indent=2)+'\n', encoding='utf-8', newline='\n')

p = r/'tools/probe_graphics_v110.inc'
s = p.read_text(encoding='utf-8')
marker = '    const char *wifi_assets[]='
assert s.count(marker) == 1
s = s.replace(marker, '''    const char *framework_profiles[]={"i18n_service.json","service_router.json","download_server.json"};
    for(unsigned i=0;i<sizeof(framework_profiles)/sizeof(framework_profiles[0]);i++){
        char source[256],target[256];snprintf(source,sizeof(source),"/graphics/%s",framework_profiles[i]);
        snprintf(target,sizeof(target),"/hmos-root/system/profile/%s",framework_profiles[i]);
        if(copy_ram_asset(source,target,0644)<0)return -1;
    }
'''+marker)
p.write_text(s, encoding='utf-8', newline='\n')
p = d/'start-native-desktop-v110.sh'
s = p.read_text(encoding='utf-8')
marker = 'stage=media\n'
assert s.count(marker) == 1
s = s.replace(marker, '''stage=framework
$B chroot "$R" /system/bin/param set sheng.debug.start.framework true
for id in 1602 404 3706; do
 deadline=$(($(now)+8))
 while ! $B timeout 3 $B chroot "$R" /compat/bin/native_sa_check "$id"; do
  if [ "$(now)" -ge "$deadline" ]; then echo "FRAMEWORK_PROVIDER_NOT_READY=$id"; break; fi
  $B sleep 1
 done
done
'''+marker)
p.write_text(s, encoding='utf-8', newline='\n')
(r/'tools/start_native_desktop_v110.sh').write_text(s, encoding='utf-8', newline='\n')

p = r/'tools/verify_v110.py'
s = p.read_text(encoding='utf-8').replace('apply-memmgr-v1.sh', 'apply-memmgr-v2.sh').replace('sheng-framework/memmgr-v1/', 'sheng-framework/memmgr-v2/')
s = s.replace("'memmgrservice','sheng_memmgr_check'}", "'memmgrservice','sheng_memmgr_check','i18n_service','service_router','download_server'}")
s = s.replace("'process.cfg','timeservice.cfg']:", "'process.cfg','timeservice.cfg','i18n_service.cfg','srms.cfg','downloadservice.cfg']:")
marker = " assert b'start-wifi-v110.sh' in binary"
assert s.count(marker) == 1
s = s.replace(marker, ''' for profile, sa in [('i18n_service.json',1602),('service_router.json',404),('download_server.json',3706)]:
  c=json.loads(new['graphics/'+profile][1]);o=json.loads((root/'work/hmos_system/system/system/profile'/profile).read_text(encoding='utf-8'));o['systemability'][0]['run-on-create']=True
  assert c==o and c['systemability'][0]['name']==sa
 assert b'sheng.debug.start.framework true' in new['graphics/start-native-desktop-v110.sh'][1]
 assert b'apply-memmgr-v1.sh' not in new['graphics/apply-runtime-v110.sh'][1]
 assert 'graphics/apply-memmgr-v1.sh' not in new
'''+marker)
p.write_text(s, encoding='utf-8', newline='\n')
print('v110 prepared: guarded real MemAvailable KB + original I18n/router/download providers')
