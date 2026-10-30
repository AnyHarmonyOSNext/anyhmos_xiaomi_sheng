"""Remove the interaction GPU policy and restore the verified v88 120Hz VDI."""
from pathlib import Path
import json
import shutil

r = Path(__file__).resolve().parent.parent
d = r / 'compat/sheng-graphics/v91'
assert not d.exists()
shutil.copytree(r / 'compat/sheng-graphics/v90', d)
for p in list(d.iterdir()):
    if p.is_file() and p.suffix in {'.sh', '.cfg'}:
        q = p.with_name(p.name.replace('v90', 'v91'))
        text = p.read_text(encoding='utf-8').replace('v90', 'v91').replace('V90', 'V91')
        if q != p:
            p.unlink()
        q.write_text(text, encoding='utf-8', newline='\n')
(d / 'sheng_gpu_policy').unlink()
shutil.copy2(r / 'compat/sheng-graphics/framepacing-v1/libdisplay_composer_vdi_impl.z.so',
             d / 'libdisplay_composer_vdi_impl.z.so')
p = d / 'init-desktop-services.cfg'
c = json.loads(p.read_text(encoding='utf-8'))
c['services'] = [s for s in c['services'] if s['name'] != 'sheng_gpu_policy']
c['jobs'] = [j for j in c['jobs'] if 'gpu-policy' not in j['name']]
p.write_text(json.dumps(c, indent=2) + '\n', encoding='utf-8', newline='\n')
p = d / 'apply-hardware-v91.sh'
s = p.read_text(encoding='utf-8').replace('hardware_observe sheng_gpu_policy ', 'hardware_observe ')
s = s[:s.index(': > $R/data/local/tmp/sheng-gpu-policy.txt')]
s += '$B touch $R/data/local/tmp/sheng-gpu-policy-disabled\n'
p.write_text(s, encoding='utf-8', newline='\n')
p = d / 'start-graphics-v91.sh'
s = p.read_text(encoding='utf-8')
s = s.replace('$B chroot $R /system/bin/param set sheng.debug.start.gpu-policy true\n', '')
p.write_text(s, encoding='utf-8', newline='\n')
for name in ['hmos_probe_v90.c', 'probe_graphics_v90.inc', 'probe_command_v90.inc',
             'build_probe_v90.py', 'verify_v90.py', 'start_native_desktop_v90.sh']:
    s = (r / 'tools' / name).read_text(encoding='utf-8').replace('v90', 'v91')
    if name == 'verify_v90.py':
        s = s.replace('static144-v1/libdisplay_composer', 'framepacing-v1/libdisplay_composer')
        s = s.replace(",'sheng_gpu_policy'}", "}")
        s = s.replace(" assert new['graphics/sheng_gpu_policy'][1]==(root/'compat/sheng-graphics/gpu-policy-v2/sheng_gpu_policy').read_bytes()",
                      " assert 'graphics/sheng_gpu_policy' not in new\n assert b'sheng_gpu_policy' not in new['graphics/init-desktop-services.cfg'][1]\n assert b'sheng.debug.start.gpu-policy' not in new['graphics/start-graphics-v91.sh'][1]")
    (r / 'tools' / name.replace('v90', 'v91')).write_text(s, encoding='utf-8', newline='\n')
(r / 'tools/configs/init-core-v91.cfg').write_text(
    (r / 'tools/configs/init-core-v90.cfg').read_text(encoding='utf-8').replace('v90', 'v91'),
    encoding='utf-8', newline='\n')
print('v91: no GPU policy binary/service/job; verified v88 120Hz display VDI')
