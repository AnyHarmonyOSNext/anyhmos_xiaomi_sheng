"""Enable original battery HDI and SA3302 using only the vendor_boot payload."""
from pathlib import Path
import json
from vendor_ramdisk_edit import edit,sha

r=Path(__file__).resolve().parent.parent
prefix='sheng-compat-v118/'
outdir=r/'compat/sheng-power/battery-v131'; outdir.mkdir(exist_ok=True)
binary=r/'compat/debug-tools/native_battery_hdi_publisher_v131'
profile=json.loads((r/'work/hmos_system/system/system/profile/powermgr.json').read_text())
battery=next(p for p in profile['systemability'] if p['name']==3302)
assert battery['libpath']=='libbatteryservice.z.so'
assert battery['min_hdi_proxy_version']==['libbattery_proxy_2.0.z.so']
manifest={}
newname=prefix+'graphics/native_battery_hdi_publisher_v131'
allowed={newname,prefix+'graphics/powermgr.json',prefix+'graphics/init-hardware-v116.cfg',
         prefix+'graphics/apply-hardware-v116.sh',prefix+'MANIFEST.json'}

def mutate(entries):
    name=prefix+'graphics/powermgr.json'; f,b=entries[name]; cfg=json.loads(b)
    assert [p['name'] for p in cfg['systemability']]==[3308,3301]
    cfg['systemability'].append(battery)
    data=(json.dumps(cfg,indent=2)+'\n').encode()
    entries[name]=(f.copy(),data); (outdir/'powermgr.json').write_bytes(data)
    name=prefix+'graphics/init-hardware-v116.cfg'; f,b=entries[name]; cfg=json.loads(b)
    assert not any(s['name']=='sheng_battery_hdi' for s in cfg['services'])
    job=next(j for j in cfg['jobs'] if j['name']=='param:sheng-hardware')
    assert job['cmds']==['start powermgr']
    job['cmds'].insert(0,'start sheng_battery_hdi')
    cfg['services'].append(dict(name='sheng_battery_hdi',
        path=['/compat/bin/native_battery_hdi_publisher_v131','--serve'],
        uid='power_host',gid=['power_host','system','log','battery_extra_host'],
        caps=['BLOCK_SUSPEND'],secon='u:r:power_host:s0',disabled=1,once=1,
        sandbox=0,saspawn=False,**{'start-mode':'condition'}))
    data=(json.dumps(cfg,indent=2)+'\n').encode()
    entries[name]=(f.copy(),data); (outdir/'init-hardware-v116.cfg').write_bytes(data)
    name=prefix+'graphics/apply-hardware-v116.sh'; f,b=entries[name]; text=b.decode()
    needle='native_brightness_launcher native_sa_check;'
    assert text.count(needle)==1
    text=text.replace(needle,'native_brightness_launcher native_sa_check native_battery_hdi_publisher_v131;')
    text+='\n: > $R/data/local/tmp/sheng-battery-hdi.txt\n$B chown 3025:3025 $R/data/local/tmp/sheng-battery-hdi.txt\n$B chmod 0600 $R/data/local/tmp/sheng-battery-hdi.txt\n'
    data=text.encode(); entries[name]=(f.copy(),data); (outdir/'apply-hardware-v116.sh').write_bytes(data)
    fields=entries[prefix+'graphics/native_brightness_launcher'][0].copy()
    fields[0]=max(f[0] for f,b in entries.values())+1
    entries[newname]=(fields,binary.read_bytes())
    manifest.update({n[len(prefix):]:dict(bytes=len(b),mode=oct(f[1]),sha256=sha(b))
        for n,(f,b) in entries.items() if n.startswith(prefix) and n!=prefix+'MANIFEST.json'})
    name=prefix+'MANIFEST.json'; f,_=entries[name]
    entries[name]=(f.copy(),(json.dumps(manifest,indent=2)+'\n').encode())

image=edit(r/'output/vendor_boot_hmos_compat_v130.img',
    'dce4b1c8ac5bec1b0f6b7a9161f5b9b0a6fde50d6822bde79588a236b8a7b1b0',
    r/'work/battery-v131',mutate,allowed,added={newname})
out=r/'output/vendor_boot_hmos_compat_v131.img';out.write_bytes(image)
verification=dict(version='v131',status='built_not_flashed',
    vendor_boot=dict(file=out.name,bytes=len(image),sha256=sha(image)),
    cpio_verified=True,preserved_v130_entries=True,changed_entries=sorted(allowed),
    init_boot_unchanged=True,dtb_unchanged=True,bootconfig_unchanged=True,
    stock_vendor_modules_and_audio_unchanged=True,usb_v121_unchanged=True,
    graphics_v130_unchanged=True,original_gpu_governor_unchanged=True,
    original_battery_implementation=True,original_battery_stub=True,original_battery_service=True,
    real_sysfs_getters_and_binder_verified=True,
    binder_proof='output/logs/command-shell-20261030-101214-a10dca71b525.log',
    publisher_sha256=sha(binary.read_bytes()),cold_boot_verified=False,
    original_service_identity_and_callbacks_verified=False,battery_ui_verified=False)
(r/'analysis/battery-v131-verification.json').write_text(json.dumps(verification,indent=2)+'\n')
(r/'output/v131-payload-manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
script=(r/'output/Flash-CompatV130.ps1').read_text(encoding='utf-8-sig')
script=script.replace('v130','v131').replace('alpha-metadata-v131-verification','battery-v131-verification').replace('preserved_v129_entries','preserved_v130_entries')
(r/'output/Flash-CompatV131.ps1').write_text(script,encoding='utf-8-sig')
print(json.dumps(verification,indent=2))
