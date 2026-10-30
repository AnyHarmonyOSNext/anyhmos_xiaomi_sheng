"""Complete v99's WLAN HDF host using the original donor chip controller."""
from pathlib import Path
import json
import shutil
import subprocess

r = Path(__file__).resolve().parent.parent
d = r/'compat/sheng-graphics/v100'
assert not d.exists()
shutil.copytree(r/'compat/sheng-graphics/v99', d)
for p in list(d.iterdir()):
    if p.is_file() and p.suffix in {'.sh', '.cfg'}:
        q = p.with_name(p.name.replace('v99', 'v100'))
        content = p.read_text(encoding='utf-8').replace('v99', 'v100').replace('V99', 'V100')
        if p != q: p.unlink()
        q.write_text(content, encoding='utf-8', newline='\n')
for name in ['hmos_probe_v99.c', 'probe_graphics_v99.inc', 'probe_command_v99.inc',
             'build_probe_v99.py', 'verify_v99.py', 'start_native_desktop_v99.sh']:
    (r/'tools'/name.replace('v99', 'v100')).write_text(
        (r/'tools'/name).read_text(encoding='utf-8').replace('v99', 'v100'),
        encoding='utf-8', newline='\n')
(r/'tools/configs/init-core-v100.cfg').write_text(
    (r/'tools/configs/init-core-v99.cfg').read_text().replace('v99', 'v100'), newline='\n')
# Keep the delayed-netdev fix discovered during the v99 real boot.
(d/'start-wifi-v100.sh').write_text(
    (r/'compat/firmware-contract/start-wifi-v99.sh').read_text().replace('v99', 'v100'), newline='\n')
profile = json.loads((r/'work/hmos_system/system/system/profile/wifi_manager_service.json').read_text())
for sa in profile['systemability']:
    sa['run-on-create'] = sa['name'] in [1120, 1124, 1126]
(d/'wifi-manager-eager.json').write_text(json.dumps(profile, indent=2)+'\n', newline='\n')
p = r/'tools/probe_graphics_v100.inc'
src = p.read_text()
marker = '    const char *wifi_assets[]='
assert src.count(marker) == 1
src = src.replace(marker,
    '    if(copy_ram_asset("/graphics/wifi-manager-eager.json",'
    '"/hmos-root/system/profile/wifi_manager_service.json",0644)<0)return -1;\n'+marker)
p.write_text(src, newline='\n')
hcs = (r/'tools/configs/sheng-graphics-v99.hcs').read_text()
marker = '            wifi_device {\n'
assert hcs.count(marker) == 1
chip = '''            chip_device {
                device0 {
                    policy = 2;
                    priority = 90;
                    moduleName = "libchip_hdi_driver.z.so";
                    serviceName = "chip_interface_service";
                    preload = 0;
                    permission = 0664;
                    deviceMatchAttr = "";
                }
            }
'''
hcs = hcs.replace(marker, chip+marker)
(r/'tools/configs/sheng-graphics-v100.hcs').write_text(hcs, newline='\n')
w = '/mnt/c/SHENG_WORKSPACE'
subprocess.run(['wsl', '-d', 'Ubuntu-22.04', '--', '/root/hmos-work/graphics-deps/hc-gen',
                '-o', w+'/compat/sheng-graphics/v100/hdf_default.hcb',
                w+'/tools/configs/sheng-graphics-v100.hcs'], check=True)
p = r/'tools/verify_v100.py'
src = p.read_text()
marker = " assert b'start-wifi-v100.sh' in binary"
assert src.count(marker) == 1
src = src.replace(marker, ''' profile=json.loads(new['graphics/wifi-manager-eager.json'][1])
 assert {x['name'] for x in profile['systemability'] if x['run-on-create']}=={1120,1124,1126}
 assert b'chip_interface_service' in new['hmos-hdf-graphics.hcb'][1]
 assert b'WIFI_NETDEV_WAIT_SECONDS' in new['graphics/start-wifi-v100.sh'][1]
'''+marker)
p.write_text(src, newline='\n')
print('v100 prepared: chip controller + eager WLAN SA profile; no vendor/audio/GPU changes')
