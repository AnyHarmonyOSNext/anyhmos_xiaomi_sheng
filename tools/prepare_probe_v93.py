"""Use a deliberately provisioned physical userdata filesystem, never a loop image."""
from pathlib import Path
import shutil

r = Path(__file__).resolve().parent.parent
d = r / 'compat/sheng-graphics/v93'
assert not d.exists()
shutil.copytree(r / 'compat/sheng-graphics/v92', d)
for p in list(d.iterdir()):
    if p.is_file() and p.suffix in {'.sh', '.cfg'}:
        q = p.with_name(p.name.replace('v92', 'v93'))
        s = p.read_text(encoding='utf-8').replace('v92', 'v93').replace('V92', 'V93')
        if q != p:
            p.unlink()
        q.write_text(s, encoding='utf-8', newline='\n')
for name in ['hmos_probe_v92.c', 'probe_graphics_v92.inc', 'probe_command_v92.inc',
             'build_probe_v92.py', 'verify_v92.py', 'start_native_desktop_v92.sh']:
    s = (r / 'tools' / name).read_text(encoding='utf-8').replace('v92', 'v93')
    (r / 'tools' / name.replace('v92', 'v93')).write_text(s, encoding='utf-8', newline='\n')
(r / 'tools/configs/init-core-v93.cfg').write_text(
    (r / 'tools/configs/init-core-v92.cfg').read_text(encoding='utf-8').replace('v92', 'v93'),
    encoding='utf-8', newline='\n')
for name in ['init-persistent-ext4.sh', 'init-ram-ext4.sh']:
    (d / name).unlink()
shutil.copyfile(r / 'tools/init-userdata-ext4.sh', d / 'init-userdata-ext4.sh')

p = r / 'tools/hmos_probe_v93.c'
s = p.read_text(encoding='utf-8')
s = s.replace('"/sheng-persistent/hmos-compat/identity"', '"/hmos-root/data/.sheng-userdata-layout"')
s = s.replace('"sheng-hmos-data-v1\\n76fb5f0c-a521-4461-948d-60f2204655dc\\n"',
              '"sheng-userdata-direct-v1\\n57275cef-3a0e-427c-a22e-66ca7e80b893\\n851324555264\\n"')
s = s.replace('"/sheng-persistent/hmos-compat/probe-%s.log"', '"/hmos-root/data/local/tmp/probe-%s.log"')
s = s.replace('/* System upper layers are RAM-backed; /data is the existing ext4 file.\n     * Only read-only logical devices are exposed in the native root. */',
              '/* System upper layers are RAM-backed; physical userdata supplies /data.\n     * Logical devices remain read-only; userdata was provisioned in Recovery. */')
s = s.replace('/* A separately prepared ext4 image provides persistent framework data. */',
              '/* Mount only the explicitly provisioned whole userdata partition. */')
s = s.replace('/graphics/init-persistent-ext4.sh', '/graphics/init-userdata-ext4.sh')
s = s.replace('# Mounted by sheng debug bootstrap; no physical userdata access.\\n',
              '# Physical userdata already mounted by sheng bootstrap; never format here.\\n')
s = s.replace('RAM overlays, persistent ext4 data, RAM metadata, no physical userdata node inside native root',
              'RAM overlays, direct whole-partition ext4 userdata, RAM metadata')
p.write_text(s, encoding='utf-8', newline='\n')
p = r / 'tools/verify_v93.py'
s = p.read_text(encoding='utf-8').replace("assert b'init-persistent-ext4.sh' in binary", """assert b'init-userdata-ext4.sh' in binary
 assert b'init-persistent-ext4.sh' not in binary
 assert 'graphics/init-persistent-ext4.sh' not in new
 assert 'graphics/init-ram-ext4.sh' not in new
 userdata = new['graphics/init-userdata-ext4.sh'][1]
 assert b'57275cef-3a0e-427c-a22e-66ca7e80b893' in userdata
 assert b'851324555264' in userdata
 for forbidden in [b'losetup', b'loop7', b'data-v1.ext4', b'mke2fs', b'mkfs']:
  assert forbidden not in userdata, forbidden
 assert b'mount -t ext4' in userdata and b'PARTNAME=userdata' in userdata
 assert b'.sheng-userdata-layout' in userdata and b'ro,nosuid,nodev,noatime' in userdata""")
p.write_text(s, encoding='utf-8', newline='\n')
print('v93 direct userdata baseline staged; no partition changed')
