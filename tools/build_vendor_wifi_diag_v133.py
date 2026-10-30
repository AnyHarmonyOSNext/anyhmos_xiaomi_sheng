"""Add an opt-in, permission-declared original-API Wi-Fi diagnostic service."""
from pathlib import Path
import json, subprocess
from vendor_ramdisk_edit import edit, sha

r=Path(__file__).resolve().parent.parent
prefix='sheng-compat-v118/'
base=r/'output/vendor_boot_hmos_compat_v132.img'
binary=(r/'compat/debug-tools/native_wifi_link_v133').read_bytes()
build=json.loads((r/'analysis/wifi-link-probe-v133.json').read_text())
assert len(binary)==build['bytes'] and sha(binary)==build['sha256']
assert binary[:4]==b'\x7fELF'
cfgname=prefix+'graphics/init-hardware-v116.cfg'
applyname=prefix+'graphics/apply-hardware-v116.sh'
binname=prefix+'graphics/native_wifi_link_v133'
manifestname=prefix+'MANIFEST.json'
manifest={}

def mutate(es):
    f,b=es[cfgname];cfg=json.loads(b)
    assert not any(s['name']=='sheng_wifi_link_probe_v133' for s in cfg['services'])
    cfg['services'].append(dict(name='sheng_wifi_link_probe_v133',
        path=['/compat/bin/native_wifi_link_v133','--service'], uid='shell',gid=['shell'],
        permission=['ohos.permission.GET_WIFI_INFO'],apl='system_basic',
        disabled=1,once=1,sandbox=0,saspawn=False,**{'start-mode':'condition'}))
    cfg['jobs'].append(dict(name='param:sheng-wifi-link-query-v133',
        condition='sheng.debug.query.wifi=true',cmds=['start sheng_wifi_link_probe_v133']))
    es[cfgname]=(f.copy(),(json.dumps(cfg,indent=2)+'\n').encode())
    f,b=es[applyname];script=b.decode()
    marker='native_sa_check native_battery_hdi_publisher_v131; do'
    assert script.count(marker)==1
    script=script.replace(marker,'native_sa_check native_battery_hdi_publisher_v131 native_wifi_link_v133; do')
    script+='''
# Explicit query only; init grants the declared GET_WIFI_INFO permission.
: > $R/data/local/tmp/sheng-wifi-link-v133.txt
$B chown 2000:2000 $R/data/local/tmp/sheng-wifi-link-v133.txt
$B chmod 0600 $R/data/local/tmp/sheng-wifi-link-v133.txt
'''
    es[applyname]=(f.copy(),script.encode())
    f,_=es[prefix+'graphics/native_battery_hdi_publisher_v131']
    es[binname]=(f.copy(),binary)
    manifest.update({n[len(prefix):]:dict(bytes=len(b),mode=oct(f[1]),sha256=sha(b))
        for n,(f,b) in es.items() if n.startswith(prefix) and n!=manifestname})
    f,_=es[manifestname]
    es[manifestname]=(f.copy(),(json.dumps(manifest,indent=2)+'\n').encode())

allowed={cfgname,applyname,binname,manifestname}
image=edit(base,'42f59b550cca6bda6a2fbdcf260771ff12d07ba4a1384eaee5bd1df62b64342f',
    r/'work/wifi-diag-v133',mutate,allowed,added={binname})
out=r/'output/vendor_boot_hmos_compat_v133.img';out.write_bytes(image)
verification=dict(version='v133',status='built_not_flashed',
    vendor_boot=dict(file=out.name,bytes=len(image),sha256=sha(image)),
    cpio_verified=True,preserved_v132_entries=True,changed_entries=sorted(allowed),
    init_boot_unchanged=True,dtb_unchanged=True,bootconfig_unchanged=True,
    stock_vendor_modules_and_audio_unchanged=True,usb_v121_unchanged=True,
    graphics_v130_unchanged=True,battery_v131_unchanged=True,startup_video_v132_unchanged=True,
    wifi_connection_state_unchanged=True,permissions_not_bypassed=True,
    service_opt_in_only=True,cold_boot_verified=False,native_api_query_verified=False)
(r/'analysis/wifi-diag-v133-verification.json').write_text(json.dumps(verification,indent=2)+'\n')
(r/'output/v133-payload-manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
script=(r/'output/Flash-CompatV132.ps1').read_text(encoding='utf-8-sig')
script=script.replace('v132','v133').replace('startup-video-v133-verification','wifi-diag-v133-verification').replace('preserved_v131_entries','preserved_v132_entries')
(r/'output/Flash-CompatV133.ps1').write_text(script,encoding='utf-8-sig')
print(json.dumps(verification,indent=2))
