"""Add the donor's original NWebSpawn daemon and original startup directories."""
from pathlib import Path
import json
from vendor_ramdisk_edit import edit, sha

r=Path(__file__).resolve().parent.parent
prefix='sheng-compat-v118/'
original=json.loads((r/'work/hmos_system/system/system/etc/init/nwebspawn.cfg').read_text())
svc=original['services'][0]
assert svc['name']=='nwebspawn' and svc['uid']=='nwebspawn'
assert svc['path'][0]=='/system/bin/nwebspawn' and '--sandbox-switch on' in ' '.join(svc['path'])
# Keep crashes observable rather than introducing an unbounded restart loop.
svc.update(disabled=1,once=1)
mkdirs=['mkdir /mnt/sandbox 0755 root root',
        'mkdir /mnt/sandbox/com.ohos.render 0711 nwebspawn nwebspawn',
        'mkdir /data/service/el1/startup/nwebspawn 0700 nwebspawn nwebspawn',
        'mkdir /data/service/el1/startup/log 0755 root root']
original['jobs'][0]['cmds']=mkdirs+original['jobs'][0]['cmds']
original['jobs'].append(dict(name='param:sheng.debug.start.nwebspawn',
    condition='sheng.debug.start.nwebspawn=true',
    cmds=mkdirs+['start nwebspawn','setparam sheng.debug.start.nwebspawn false']))
manifest={}
def mutate(entries):
    name=prefix+'graphics/init-desktop-services.cfg';f,b=entries[name];cfg=json.loads(b)
    assert not any(s['name']=='nwebspawn' for s in cfg['services'])
    assert not {j['name'] for j in original['jobs']} & {j['name'] for j in cfg['jobs']}
    cfg['services'].append(svc);cfg['jobs'].extend(original['jobs'])
    entries[name]=(f.copy(),(json.dumps(cfg,indent=2)+'\n').encode())
    manifest.update({n[len(prefix):]:dict(bytes=len(b),mode=oct(f[1]),sha256=sha(b))
                     for n,(f,b) in entries.items() if n.startswith(prefix) and n!=prefix+'MANIFEST.json'})
    name=prefix+'MANIFEST.json';f,_=entries[name]
    entries[name]=(f.copy(),(json.dumps(manifest,indent=2)+'\n').encode())
allowed={prefix+'graphics/init-desktop-services.cfg',prefix+'MANIFEST.json'}
image=edit(r/'output/vendor_boot_hmos_compat_v121.img',
    'f6ca4bc55aaee10a8cd4cfb6c5e0f18e7859311187aaa1cf064dcb256c9e4982',
    r/'work/nwebspawn-v122',mutate,allowed)
out=r/'output/vendor_boot_hmos_compat_v122.img';out.write_bytes(image)
report=dict(version='v122',status='built_not_flashed',
    vendor_boot=dict(file=out.name,bytes=len(image),sha256=sha(image)),
    cpio_verified=True,preserved_v121_entries=True,changed_entries=sorted(allowed),
    init_boot_unchanged=True,dtb_unchanged=True,bootconfig_unchanged=True,
    stock_vendor_modules_and_audio_unchanged=True,usb_v121_unchanged=True,
    original_nwebspawn_service=svc,original_jobs_preserved=True,cold_boot_verified=False,
    webcore_main_installed_original_bms=True,webview_content_verified=False)
(r/'analysis/nwebspawn-v122-verification.json').write_text(json.dumps(report,indent=2)+'\n')
(r/'output/v122-payload-manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
print(json.dumps(report,indent=2))
