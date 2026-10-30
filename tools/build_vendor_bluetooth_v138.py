"""Add a bounded init-owned Bluetooth diagnostic with explicit permissions."""
from pathlib import Path
import json, subprocess
from vendor_ramdisk_edit import edit,sha
r=Path(__file__).resolve().parent.parent
def wsl(p): return '/mnt/c/'+str(p).replace('\\','/').split(':/',1)[1]
sdk='/root/hmos-work/sdk-6.0.0.47/installed/native/llvm/bin/'
binary=r/'output/native_bt_host_check_v138'
subprocess.run(['wsl.exe','--',sdk+'clang','--target=aarch64-linux-ohos','-O2','-Wall','-Wextra','-Werror',wsl(r/'tools/native_bt_host_check_v137.c'),'-ldl','-o',wsl(binary)],check=True)
subprocess.run(['wsl.exe','--',sdk+'llvm-strip',wsl(binary)],check=True)
p='sheng-compat-v118/'
target=p+'bluetooth-v136/native_bt_host_check_v138'
cfg=p+'bluetooth-v136/init-bluetooth-v136.cfg'
checks=p+'bluetooth-v136/SHA256SUMS'
apply=p+'graphics/apply-hardware-v116.sh'
manifest=p+'MANIFEST.json'
allowed={target,cfg,checks,apply,manifest}
def mutate(entries):
    field=entries[p+'bluetooth-v136/native_bt_hdi_publisher_v136'][0].copy()
    field[0]=max(f[0] for f,b in entries.values())+1
    entries[target]=(field,binary.read_bytes())
    f,b=entries[cfg];c=json.loads(b)
    c['services'].append(dict(name='sheng_bluetooth_check',
        path=['/compat/bin/native_bt_host_check_v138','--service'],uid='shell',gid=['shell'],
        apl='system_core',permission=['ohos.permission.ACCESS_BLUETOOTH','ohos.permission.MANAGE_BLUETOOTH'],
        disabled=1,once=1,sandbox=0,saspawn=False,**{'start-mode':'condition'}))
    c['jobs'].append(dict(name='param:sheng-bluetooth-check',condition='sheng.debug.bluetooth.check=true',
        cmds=['start sheng_bluetooth_check']))
    entries[cfg]=(f.copy(),(json.dumps(c,indent=2)+'\n').encode())
    f,b=entries[apply];text=b.decode()
    marker='$B cp /compat/bluetooth-v136/native_bt_hdi_publisher_v136 $R/compat/bin/\n'
    assert text.count(marker)==1
    text=text.replace(marker,marker+'$B cp /compat/bluetooth-v136/native_bt_host_check_v138 $R/compat/bin/\n$B chmod 0755 $R/compat/bin/native_bt_host_check_v138\n')
    text+='\n: > $R/data/local/tmp/sheng-bluetooth-check.txt\n$B chown 2000:2000 $R/data/local/tmp/sheng-bluetooth-check.txt\n$B chmod 0600 $R/data/local/tmp/sheng-bluetooth-check.txt\n'
    entries[apply]=(f.copy(),text.encode())
    f,_=entries[checks]
    names=sorted(n for n in entries if n.startswith(p+'bluetooth-v136/') and n!=checks and (entries[n][0][1]&0o170000)==0o100000)
    entries[checks]=(f.copy(),''.join(sha(entries[n][1])+'  '+n[len(p+'bluetooth-v136/'):]+'\n' for n in names).encode())
    f,b=entries[manifest];m=json.loads(b)
    for n in allowed-{manifest}:
        fs,blob=entries[n];m[n[len(p):]]=dict(bytes=len(blob),mode=oct(fs[1]),sha256=sha(blob))
    entries[manifest]=(f.copy(),(json.dumps(m,indent=2)+'\n').encode())
image=edit(r/'output/vendor_boot_hmos_compat_v137.img','208c92fbc54c77831faa5446705720e178af14a1edf3d898874497d92d4d1539',r/'work/bluetooth-persistent-v138',mutate,allowed,added={target})
out=r/'output/vendor_boot_hmos_compat_v138.img';out.write_bytes(image)
v=json.loads((r/'analysis/bluetooth-v137-verification.json').read_text())
v.update(version='v138',status='built_not_flashed',preserved_v137_entries=True,changed_entries=sorted(allowed),vendor_boot=dict(file=out.name,bytes=len(image),sha256=sha(image)),explicit_diagnostic_permission=True)
(r/'analysis/bluetooth-v138-verification.json').write_text(json.dumps(v,indent=2)+'\n')
flash=(r/'output/Flash-CompatV137.ps1').read_text(encoding='utf-8-sig').replace('v137','v138').replace('preserved_v136_entries','preserved_v137_entries')
(r/'output/Flash-CompatV138.ps1').write_text(flash,encoding='utf-8-sig')
print(json.dumps(v,indent=2))
