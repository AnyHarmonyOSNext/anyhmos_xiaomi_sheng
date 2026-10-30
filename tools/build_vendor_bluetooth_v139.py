"""Persist verified port-ready contract and import original Fusion frontend."""
from pathlib import Path
import json,copy
from vendor_ramdisk_edit import edit,sha
r=Path(__file__).resolve().parent.parent
p='sheng-compat-v118/'
cfg=p+'bluetooth-v136/init-bluetooth-v136.cfg'
start=p+'bluetooth-v136/start-bluetooth-v136.sh'
checks=p+'bluetooth-v136/SHA256SUMS'
apply=p+'graphics/apply-hardware-v116.sh'
manifest=p+'MANIFEST.json'
target=p+'bluetooth-v136/native_bt_host_check_v139'
allowed={cfg,start,checks,apply,manifest,target}
def mutate(entries):
    f=entries[p+'bluetooth-v136/native_bt_host_check_v138'][0].copy()
    f[0]=max(fs[0] for fs,b in entries.values())+1
    entries[target]=(f,(r/'output/native_bt_host_check_v139').read_bytes())
    f,b=entries[cfg];c=json.loads(b)
    diag=next(s for s in c['services'] if s['name']=='sheng_bluetooth_check')
    diag['path'][0]='/compat/bin/native_bt_host_check_v139'
    fusion=copy.deepcopy(json.loads((r/'work/hmos_system/system/system/etc/init/fusion_connectivity_manager_ext.cfg').read_text())['services'][0])
    fusion.update(disabled=1,once=1,sandbox=0,saspawn=False,**{'start-mode':'condition'})
    c['services'].append(fusion)
    native=next(j for j in c['jobs'] if j['name']=='param:sheng-bluetooth-v136')
    native['cmds'].append('start fusion_connectivity_manager_ext')
    entries[cfg]=(f.copy(),(json.dumps(c,indent=2)+'\n').encode())
    f,b=entries[apply];text=b.decode()
    marker='$B cp /compat/bluetooth-v136/native_bt_host_check_v138 $R/compat/bin/\n'
    assert text.count(marker)==1
    text=text.replace(marker,marker+'$B cp /compat/bluetooth-v136/native_bt_host_check_v139 $R/compat/bin/\n$B chmod 0755 $R/compat/bin/native_bt_host_check_v139\n')
    entries[apply]=(f.copy(),text.encode())
    f,b=entries[start];text=b.decode()
    marker='stage=native_services\n'
    assert text.count(marker)==1
    text=text.replace(marker,'''stage=port_ready_contract
# The donor sets this after its connectivity file/permission setup, not RF init.
# Apply the equivalent real Qualcomm port setup before notifying the old service.
[ "$($B stat -c '%a:%u:%g' "$R/data/vendor/bluetooth")" = 770:3021:3021 ]
[ "$($B stat -c '%a:%u:%g' "$R/data/service/el1/public/bluetooth")" = 711:1002:1002 ]
[ "$($B stat -c '%a:%u:%g' "$R/dev/unix/socket/sheng.bt.h4")" = 660:0:3021 ]
[ -c /dev/btpower ] && [ -c /dev/ttyHS0 ] && [ -S "$R/dev/unix/socket/sheng.bt.h4" ]
$B mkdir -p "$R/data/service/el1/public/fcm"
fcm_id=$($B awk -F: '$1=="fusion_connectivity_manager_ext" {print $3}' "$R/system/etc/passwd")
[ -n "$fcm_id" ]
$B chown "$fcm_id:$fcm_id" "$R/data/service/el1/public/fcm"
$B chmod 0700 "$R/data/service/el1/public/fcm"
$B chroot "$R" /system/bin/param set vendor.setup_mpxx_dir_mode success
echo BT_REAL_PORT_DIRECTORY_READY=1
stage=native_services
''')
    entries[start]=(f.copy(),text.encode())
    f,_=entries[checks]
    names=sorted(n for n in entries if n.startswith(p+'bluetooth-v136/') and n!=checks and (entries[n][0][1]&0o170000)==0o100000)
    entries[checks]=(f.copy(),''.join(sha(entries[n][1])+'  '+n[len(p+'bluetooth-v136/'):]+'\n' for n in names).encode())
    f,b=entries[manifest];m=json.loads(b)
    for n in allowed-{manifest}:
        fs,blob=entries[n];m[n[len(p):]]=dict(bytes=len(blob),mode=oct(fs[1]),sha256=sha(blob))
    entries[manifest]=(f.copy(),(json.dumps(m,indent=2)+'\n').encode())
image=edit(r/'output/vendor_boot_hmos_compat_v138.img','9de286aaa780073861950b96b9027c05f7b06202e4efd768e264edabd6bded1d',r/'work/bluetooth-persistent-v139',mutate,allowed,added={target})
out=r/'output/vendor_boot_hmos_compat_v139.img';out.write_bytes(image)
v=json.loads((r/'analysis/bluetooth-v138-verification.json').read_text())
v.update(version='v139',status='built_not_flashed',preserved_v138_entries=True,changed_entries=sorted(allowed),vendor_boot=dict(file=out.name,bytes=len(image),sha256=sha(image)),real_port_readiness_contract=True,original_fusion_service_imported=True,current_api_hot_verified=True,system_scan_hot_verified=True,cold_boot_verified=False)
(r/'analysis/bluetooth-v139-verification.json').write_text(json.dumps(v,indent=2)+'\n')
flash=(r/'output/Flash-CompatV138.ps1').read_text(encoding='utf-8-sig').replace('v138','v139').replace('preserved_v137_entries','preserved_v138_entries')
(r/'output/Flash-CompatV139.ps1').write_text(flash,encoding='utf-8-sig')
print(json.dumps(v,indent=2))
