"""Package verified hotspot and candidate sensor nonblocking RAM compatibility SDKs."""
from pathlib import Path
import hashlib
import json
import shutil
import subprocess
import sys

r = Path(__file__).resolve().parent.parent
for n in ['hmos_probe.c', 'probe_graphics.inc', 'probe_command.inc']:
    p = r / 'tools' / n
    q = r / 'tools/archive' / (p.stem + '_v68' + p.suffix)
    if not q.exists():
        shutil.copy2(p, q)
d = r / 'compat/sheng-graphics/v69'
assert not d.exists()
shutil.copytree(r / 'compat/sheng-graphics/v68', d)
for name in ['libsheng_scb_optional_sa.so', 'sceneboard-optional-sa.list']:
    (d / name).unlink()
cfg = json.loads((r / 'tools/configs/init-core-v68.cfg').read_text())
next(x for x in cfg['services'] if x['name'] == 'appspawn').pop('env')
(r / 'tools/configs/init-core-v69.cfg').write_text(json.dumps(cfg, indent=2)+'\n')
for component, lib in [('hotspot', 'libnet_tether_manager_if'), ('sensor', 'libsensor_client')]:
    subprocess.run([sys.executable, str(r / f'tools/prepare_{component}_nonblocking_patch.py')], check=True)
    data = (r / f'work/{lib}.nonblocking.z.so').read_bytes()
    report = json.loads((r / f'analysis/{component}-nonblocking-patch.json').read_text())
    assert hashlib.sha256(data).hexdigest() == report['output_sha256']
    (d / f'{lib}.z.so').write_bytes(data)
p = r / 'tools/probe_graphics.inc'
s = p.read_text()
for line in [
    '    if(copy_ram_asset("/graphics/libsheng_scb_optional_sa.so","/hmos-root/compat/lib64/libsheng_scb_optional_sa.so",0644)<0)return -1;\n',
    '    if(copy_ram_asset("/graphics/sceneboard-optional-sa.list","/hmos-root/compat/etc/sceneboard-optional-sa.list",0644)<0)return -1;\n']:
    assert s.count(line) == 1
    s = s.replace(line, '')
mark = '    note("SYSTEM_AUDIO_POLICY_COMPAT_BIND: original nonblocking query for SA3009; vendor untouched");'
assert s.count(mark) == 1
lines = [mark]
for lib in ['libnet_tether_manager_if', 'libsensor_client']:
    lines += [f'    if(copy_ram_asset("/graphics/{lib}.z.so","/hmos-root/compat/lib64/{lib}.z.so",0644)<0)return -1;',
              f'    if(mount("/hmos-root/compat/lib64/{lib}.z.so","/hmos-root/system/lib64/platformsdk/{lib}.z.so",NULL,MS_BIND,NULL)<0)return -1;']
lines += ['    note("SYSTEM_OPTIONAL_SDK_COMPAT_BIND: nonblocking hotspot SA1154 and sensor SA3601; vendor untouched");']
p.write_text(s.replace(mark, '\n'.join(lines)))
p = r / 'tools/hmos_probe.c'
p.write_text(p.read_text().replace('v68', 'v69'))
for n in ['build_probe', 'verify']:
    text = (r / f'tools/{n}_v68.py').read_text().replace('v68', 'v69')
    if n == 'verify':
        marker = " assert config['import']==['/compat/etc/init-desktop-services.cfg']"
        assert text.count(marker) == 1
        checks = " assert 'env' not in next(s for s in config['services'] if s['name']=='appspawn')\n assert 'graphics/libsheng_scb_optional_sa.so' not in new\n"
        for lib, sha in [('libnet_tether_manager_if', '6405b690bfe45d1f1567685f05ba0f7db8c54a54b3452dd8ae76b76403200b34'), ('libsensor_client', '10831009fabed206ab5badca696cb5d0fa61e94aafb2f03a9c13c40cf6781af8')]:
            checks += f" assert hashlib.sha256(new['graphics/{lib}.z.so'][1]).hexdigest()=='{sha}'\n"
        text = text.replace(marker, checks+marker)
    (r / f'tools/{n}_v69.py').write_text(text)
print('v69 candidate: hotspot verified in RAM, sensor awaits next process; ineffective preload removed')
