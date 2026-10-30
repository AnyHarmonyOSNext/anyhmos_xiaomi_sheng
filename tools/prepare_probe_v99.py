"""Add only WLAN configuration and the measured RAM-firmware load sequence to v97."""
from pathlib import Path
import copy
import json
import shutil
import subprocess

r = Path(__file__).resolve().parent.parent
d = r / 'compat/sheng-graphics/v99'
assert not d.exists()
shutil.copytree(r / 'compat/sheng-graphics/v97', d)
for p in list(d.iterdir()):
    if p.is_file() and p.suffix in {'.sh', '.cfg'}:
        q = p.with_name(p.name.replace('v97', 'v99'))
        content = p.read_text(encoding='utf-8').replace('v97', 'v99').replace('V97', 'V99')
        if q != p:
            p.unlink()
        q.write_text(content, encoding='utf-8', newline='\n')
for name in ['hmos_probe_v97.c', 'probe_graphics_v97.inc', 'probe_command_v97.inc',
             'build_probe_v97.py', 'verify_v97.py', 'start_native_desktop_v97.sh']:
    (r / 'tools' / name.replace('v97', 'v99')).write_text(
        (r / 'tools' / name).read_text(encoding='utf-8').replace('v97', 'v99'),
        encoding='utf-8', newline='\n')
core = json.loads((r/'tools/configs/init-core-v97.cfg').read_text(encoding='utf-8').replace('v97', 'v99'))
core['import'].append('/compat/etc/init-wifi-v99.cfg')
(r/'tools/configs/init-core-v99.cfg').write_text(json.dumps(core, indent=2), encoding='utf-8', newline='\n')

original = json.loads((r/'work/hmos_system/system/system/etc/init/wifi_standard.cfg').read_text())
wifi = copy.deepcopy(original['services'][0])
wifi.update(once=1, sandbox=0, saspawn=False)
hosts = []
for index, name, uid, groups in [(3, 'wifi_host', 'wifi_host', ['wifi_host', 'wifi_group']),
                                  (4, 'wpa_host', 'wifi', ['wifi', 'wifi_group', 'wifi_host'])]:
    service = dict(name=name, path=['/vendor/bin/hdf_devhost', '-i', str(index), '-n', name],
                   uid=uid, gid=groups, caps=['DAC_OVERRIDE', 'DAC_READ_SEARCH', 'NET_ADMIN', 'NET_RAW'],
                   secon='u:r:wifi_host:s0', disabled=1, once=1, sandbox=0, **{'start-mode': 'condition'})
    if name == 'wpa_host':
        service['permission'] = ['ohos.permission.ACCESS_CERT_MANAGER', 'ohos.permission.ACCESS_SYSTEM_APP_CERT']
    hosts.append(service)
jobs = [copy.deepcopy(original['jobs'][0]), dict(name='param:sheng-wifi-v99',
        condition='sheng.debug.start.wifi=true', cmds=[
            'mkdir /data/service/el1/public/wifi 0770 wifi wifi_group',
            'mkdir /data/service/el1/public/wifi/wpa_supplicant 0770 wifi wifi_group',
            'mkdir /data/service/el1/public/wifi/sockets 0770 wifi wifi_group',
            'mkdir /data/service/el1/public/dhcp 0770 dhcp dhcp',
            'start wifi_host', 'start wpa_host', 'start wifi_manager_service'])]
(d/'init-wifi-v99.cfg').write_text(json.dumps(dict(jobs=jobs, services=[wifi, *hosts]), indent=2),
                                 encoding='utf-8', newline='\n')
for target in ['cnss2', 'qrtr-mhi', 'qca_cld3_kiwi_v2']:
    shutil.copyfile(r/f'output/load-official303-{target}.sh', d/f'load-official303-{target}.sh')
shutil.copyfile(r/'compat/firmware-contract/stage-wifi-ram.sh', d/'stage-wifi-ram.sh')
shutil.copyfile(r/'compat/firmware-contract/start-wifi-v99.sh', d/'start-wifi-v99.sh')
shutil.copyfile(r/'output/official303-wlan-configs.tar.gz', d/'official303-wlan-configs.tar.gz')
shutil.copyfile(r/'compat/debug-tools/nl80211_probe', d/'nl80211_probe')
shutil.copyfile(r/'compat/debug-tools/native_wifi_hal_probe', d/'native_wifi_hal_probe')

# Same three existing hosts and identities. New hosts have no automatic preload;
# explicit HDF service requests can load them after the measured kernel sequence.
hcs = (r/'tools/configs/sheng-graphics-v73.hcs').read_text()
mark = '    }\n}\n'
assert hcs.endswith(mark)
extra = '''        sheng_wifi {
            hostName = "wifi_host";
            priority = 50;
            wifi_device {
                device0 {
                    policy = 2;
                    priority = 100;
                    moduleName = "libwifi_hdi_c_device.z.so";
                    serviceName = "wlan_interface_service";
                    preload = 1;
                    permission = 0664;
                    deviceMatchAttr = "";
                }
            }
        }
        sheng_wpa {
            hostName = "wpa_host";
            priority = 50;
            wpa_device {
                device0 {
                    policy = 2;
                    priority = 100;
                    moduleName = "libwpa_hdi_c_device.z.so";
                    serviceName = "wpa_interface_service";
                    preload = 1;
                    permission = 0664;
                    deviceMatchAttr = "";
                }
            }
        }
'''
(r/'tools/configs/sheng-graphics-v99.hcs').write_text(hcs[:-len(mark)] + extra + mark,
                                                   encoding='utf-8', newline='\n')
wslroot = '/mnt/c/SHENG_WORKSPACE'
subprocess.run(['wsl', '-d', 'Ubuntu-22.04', '--', '/root/hmos-work/graphics-deps/hc-gen',
                '-o', wslroot+'/compat/sheng-graphics/v99/hdf_default.hcb',
                wslroot+'/tools/configs/sheng-graphics-v99.hcs'], check=True)

# Only stage files into /compat; the original vendor mounts are untouched.
p = r/'tools/probe_graphics_v99.inc'
content = p.read_text()
mark = '    const char *render_logs[]='
assert content.count(mark) == 1
copying = '''    const char *wifi_assets[]={"init-wifi-v99.cfg","stage-wifi-ram.sh","load-official303-cnss2.sh","load-official303-qrtr-mhi.sh","load-official303-qca_cld3_kiwi_v2.sh","official303-wlan-configs.tar.gz","start-wifi-v99.sh","nl80211_probe","native_wifi_hal_probe"};
    for(unsigned i=0;i<sizeof(wifi_assets)/sizeof(wifi_assets[0]);i++){
        char source[256],target[256];snprintf(source,sizeof(source),"/graphics/%s",wifi_assets[i]);
        snprintf(target,sizeof(target),"/hmos-root/compat/%s/%s",strstr(wifi_assets[i],".cfg")?"etc":"bin",wifi_assets[i]);
        if(copy_ram_asset(source,target,0755)<0)return -1;
    }
'''
p.write_text(content.replace(mark, copying + mark), encoding='utf-8', newline='\n')

# Preserve v97's autonomous UI sequence. Wireless is explicitly started after
# cold-boot UI acceptance, rather than mixing first validation into bootstrap.
verify = r/'tools/verify_v99.py'
content = verify.read_text().replace(
    "assert config['import']==['/compat/etc/init-desktop-services.cfg','/compat/etc/init-hardware-v99.cfg']",
    "assert config['import']==['/compat/etc/init-desktop-services.cfg','/compat/etc/init-hardware-v99.cfg','/compat/etc/init-wifi-v99.cfg']")
content = content.replace("assert b'apply-preload.sh' in binary", """wireless=json.loads(new['graphics/init-wifi-v99.cfg'][1])
 assert {s['name'] for s in wireless['services']}=={'wifi_manager_service','wifi_host','wpa_host'}
 assert next(s for s in wireless['services'] if s['name']=='wifi_manager_service')['permission']==json.loads((root/'work/hmos_system/system/system/etc/init/wifi_standard.cfg').read_text())['services'][0]['permission']
 assert b'sheng.debug.start.audio true' not in new['graphics/start-native-desktop-v99.sh'][1]
 assert b'start-wifi-v99.sh' in binary
 assert b'apply-preload.sh' in binary""")
verify.write_text(content, encoding='utf-8', newline='\n')
print('v99 staged from v97: WLAN-only additions, no audio/GPU/wake/userdata changes')
