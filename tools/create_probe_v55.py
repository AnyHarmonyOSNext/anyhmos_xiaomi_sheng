"""Freeze v54 and stage persistent /data plus the runtime storage fixes."""
from pathlib import Path
import shutil
import json
r = Path(__file__).resolve().parent.parent
for name in ['hmos_probe.c', 'probe_graphics.inc', 'probe_command.inc']:
    src = r / 'tools' / name
    dst = r / 'tools/archive' / (src.stem + '_v54' + src.suffix)
    if not dst.exists():
        shutil.copy2(src, dst)
d = r / 'compat/sheng-graphics/v55'
assert not d.exists(), 'Do not overwrite an existing version'
shutil.copytree(r / 'compat/sheng-graphics/v54', d)
base = r / 'compat/sheng-framework/account-hmac-v1'
for name in ['storage-ram-launcher', 'libsheng_ram_no_tee.so']:
    shutil.copy2(base / name, d / name)
shutil.copy2(r / 'compat/sheng-framework/persistent-v1/init-persistent-ext4.sh', d / 'init-persistent-ext4.sh')
cfg = json.loads((r / 'tools/configs/init-core-v54.cfg').read_text())
pre = next(j for j in cfg['jobs'] if j['name'] == 'pre-init')['cmds']
parents = [f'mkdir /data/{base}/{level} 0711 root root'
           for base in ['service', 'chipset', 'app', 'misc']
           for level in ['el1', 'el2', 'el3', 'el4', 'el5']]
pre[0:0] = parents
(r / 'tools/configs/init-core-v55.cfg').write_bytes((json.dumps(cfg, indent=2) + '\n').encode())
p = r / 'tools/probe_graphics.inc'
s = p.read_text()
mark = '    if(copy_ram_asset("/graphics/init-desktop-services.cfg"'
assert s.count(mark) == 1
s = s.replace(mark, '    if(copy_ram_asset("/graphics/libsheng_ram_no_tee.so","/hmos-root/compat/lib64/libsheng_ram_no_tee.so",0644)<0)return -1;\n' + mark)
p.write_text(s)
p = r / 'tools/hmos_probe.c'
s = p.read_text().replace('v54', 'v55')
s = s.replace('/graphics/init-ram-ext4.sh', '/graphics/init-persistent-ext4.sh')
s = s.replace('/* RAM ext4 supplies real xattrs for the native framework; no userdata. */',
              '/* A separately prepared ext4 image provides persistent framework data. */')
s = s.replace('RAM data/metadata, read-only logical devices, no physical userdata node',
              'persistent ext4 data, RAM metadata, no physical userdata node inside native root')
s = s.replace('no OS handoff, no userdata access', 'no OS handoff, userdata access only on explicit hmos')
p.write_text(s)
for name in ['build_probe', 'verify']:
    src = (r / f'tools/{name}_v54.py').read_text().replace('v54', 'v55')
    if name == 'verify':
        src = src.replace(" assert len(new['hmos-init-debug.cfg'][1])<32768",
                          " assert b'init-persistent-ext4.sh' in binary\n assert 'graphics/libsheng_ram_no_tee.so' in new\n assert len(new['hmos-init-debug.cfg'][1])<32768")
    (r / f'tools/{name}_v55.py').write_text(src)
print('v55 staged: persistent ext4 data, parent dirs, optional HDI bridge, vendor unchanged')
