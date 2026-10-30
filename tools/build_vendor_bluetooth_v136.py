"""Add the verified original-HAL H4 transport and original OHOS service to v135."""
from pathlib import Path
import json,subprocess,copy
from vendor_ramdisk_edit import edit,sha
r=Path(__file__).resolve().parent.parent
prefix='sheng-compat-v118/'
outdir=r/'compat/sheng-bluetooth/persistent-v136';outdir.mkdir(exist_ok=True)
files={f'lib64/{p.name}':p.read_bytes() for p in (r/'compat/sheng-bluetooth/backend-v136/lib64').iterdir() if p.is_file()}
files.update({
 'libsheng_bt_bridge_v136.so':(r/'output/libsheng_bt_bridge_v136.so').read_bytes(),
 'ohos/libbt_vendor.z.so':(r/'output/libbt_vendor_sheng_v136.so').read_bytes(),
 'native_bt_hdi_publisher_v136':(r/'output/native_bt_hdi_publisher_v136').read_bytes(),
 'start-bluetooth-v136.sh':(r/'tools/start_bluetooth_v136.sh').read_bytes(),
})
for name in ('btpower','msm_geni_serial'):
 files[f'load-official303-{name}.sh']=(r/f'output/load-official303-{name}.sh').read_bytes()
service=copy.deepcopy(json.loads((r/'work/hmos_system/system/system/etc/init/bluetooth_service.cfg').read_text())['services'][0])
service.pop('ondemand');service.pop('jobs')
service.update(path=['/system/bin/sa_main','/compat/etc/bluetooth_service_v136.json'],
 disabled=1,once=1,sandbox=0,saspawn=False,**{'start-mode':'condition'})
publisher=dict(name='sheng_bluetooth_hdi',path=['/compat/bin/native_bt_hdi_publisher_v136','--serve'],
 uid='blue_host',gid=['blue_host','bluetooth','system','log'],caps=['BLOCK_SUSPEND','SYS_NICE'],
 secon='u:r:blue_host:s0',disabled=1,once=1,sandbox=0,saspawn=False,
 env=[dict(name='LD_LIBRARY_PATH',value='/compat/bluetooth-v136/ohos:/system/lib64:/vendor/lib64')],
 **{'start-mode':'condition'})
cfg=dict(services=[publisher,service],jobs=[dict(name='param:sheng-bluetooth-v136',
 condition='sheng.debug.start.bluetooth=true',cmds=['start sheng_bluetooth_hdi','start bluetooth_service'])])
files['init-bluetooth-v136.cfg']=(json.dumps(cfg,indent=2)+'\n').encode()
profile=json.loads((r/'work/hmos_system/system/system/profile/bluetooth_service.json').read_text())
assert len(profile['systemability'])==1 and profile['systemability'][0]['name']==1130
profile['systemability'][0]['run-on-create']=True
profile['systemability'][0]['auto-restart']=False
files['bluetooth_service_v136.json']=(json.dumps(profile,indent=2)+'\n').encode()
files['SHA256SUMS']=''.join(sha(b)+'  '+n+'\n' for n,b in sorted(files.items())).encode()
names={prefix+'bluetooth-v136/'+n:b for n,b in files.items()}
dirs={prefix+'bluetooth-v136',prefix+'bluetooth-v136/lib64',prefix+'bluetooth-v136/ohos'}
applyname=prefix+'graphics/apply-hardware-v116.sh'
startupname=prefix+'graphics/start-native-desktop-v116.sh'
corename=prefix+'hmos-init-debug.cfg'
allowed=set(names)|dirs|{applyname,startupname,corename,prefix+'MANIFEST.json'}
manifest={}
def syntax(path):
 wsl='/mnt/c/'+str(path).replace('\\','/').split(':/',1)[1]
 subprocess.run(['wsl.exe','--','bash','-n',wsl],check=True,capture_output=True)
def mutate(entries):
 inode=max(f[0] for f,b in entries.values())
 field=entries[prefix+'graphics/native_brightness_launcher'][0].copy()
 df=entries[prefix+'graphics'][0].copy()
 for n in sorted(dirs):
  f=df.copy();inode+=1;f[0]=inode;f[1]=0o40755;entries[n]=(f,b'')
 for n,b in names.items():
  f=field.copy();inode+=1;f[0]=inode
  f[1]=0o100755 if n.endswith('.sh') or n.endswith('native_bt_hdi_publisher_v136') else 0o100644
  entries[n]=(f,b)
 f,b=entries[corename];core=json.loads(b)
 assert '/compat/etc/init-bluetooth-v136.cfg' not in core['import']
 core['import'].append('/compat/etc/init-bluetooth-v136.cfg')
 entries[corename]=(f.copy(),(json.dumps(core,indent=2)+'\n').encode())
 f,b=entries[applyname]
 text=b.decode()+'''
# Bluetooth remains isolated from both the vendor partition and its linker.
$B mkdir -p /compat/bluetooth-v136 $R/compat/bluetooth-v136/ohos
$B cp -R /sheng-compat-v118/bluetooth-v136/. /compat/bluetooth-v136/
$B cp /compat/bluetooth-v136/ohos/libbt_vendor.z.so $R/compat/bluetooth-v136/ohos/
$B cp /compat/bluetooth-v136/native_bt_hdi_publisher_v136 $R/compat/bin/
$B chmod 0755 $R/compat/bin/native_bt_hdi_publisher_v136
for file in init-bluetooth-v136.cfg bluetooth_service_v136.json; do
 $B cp /compat/bluetooth-v136/$file $R/compat/etc/$file
done
: > $R/data/local/tmp/sheng-bluetooth-hdi.txt
$B chown 3021:3021 $R/data/local/tmp/sheng-bluetooth-hdi.txt
$B chmod 0600 $R/data/local/tmp/sheng-bluetooth-hdi.txt
'''
 path=outdir/'apply-hardware-v116.sh';path.write_text(text,encoding='utf-8',newline='\n');syntax(path)
 entries[applyname]=(f.copy(),text.encode())
 f,b=entries[startupname];text=b.decode()
 marker='''   echo "AUTOSTART_BOOTCONTROL_NOT_MARKED code=$mark_code"
  fi
 fi
 exit "$code"'''
 assert text.count(marker)==1
 replacement='''   echo "AUTOSTART_BOOTCONTROL_NOT_MARKED code=$mark_code"
  fi
  $B setsid $B timeout 75 $B sh /compat/bluetooth-v136/start-bluetooth-v136.sh > "$R/data/local/tmp/sheng-bluetooth-start-v136.txt" 2>&1 </dev/null &
  $B sleep 0.2
 fi
 exit "$code"'''
 text=text.replace(marker,replacement)
 path=outdir/'start-native-desktop-v116.sh';path.write_text(text,encoding='utf-8',newline='\n');syntax(path)
 entries[startupname]=(f.copy(),text.encode())
 manifest.update({n[len(prefix):]:dict(bytes=len(b),mode=oct(f[1]),sha256=sha(b))
  for n,(f,b) in entries.items() if n.startswith(prefix) and n!=prefix+'MANIFEST.json'})
 n=prefix+'MANIFEST.json';f,_=entries[n];entries[n]=(f.copy(),(json.dumps(manifest,indent=2)+'\n').encode())
syntax(r/'tools/start_bluetooth_v136.sh')
image=edit(r/'output/vendor_boot_hmos_compat_v135.img',
 '27327b099280e12a0540a4b8e0e179c228d74b2ba80b91869b4a132eae861749',
 r/'work/bluetooth-persistent-v136',mutate,allowed,added=set(names)|dirs)
out=r/'output/vendor_boot_hmos_compat_v136.img';out.write_bytes(image)
v=dict(version='v136',status='built_not_flashed',vendor_boot=dict(file=out.name,bytes=len(image),sha256=sha(image)),
 cpio_verified=True,preserved_v135_entries=True,changed_entries=sorted(allowed),
 init_boot_unchanged=True,dtb_unchanged=True,bootconfig_unchanged=True,
 stock_vendor_modules_and_audio_unchanged=True,usb_v121_unchanged=True,wifi_v134_unchanged=True,
 bootcontrol_v135_unchanged=True,original_gpu_governor_unchanged=True,
 original_hci_library_and_binder_proxy_verified=True,
 hci_evidence='output/logs/command-shell-20261030-130357-151f47102711.log',
 peripheral_security_development_option_process_local=True,
 cold_boot_verified=False,original_service_identity_verified=False,system_scan_and_pair_verified=False)
(r/'analysis/bluetooth-v136-verification.json').write_text(json.dumps(v,indent=2)+'\n',encoding='utf-8')
(r/'output/v136-payload-manifest.json').write_text(json.dumps(manifest,indent=2)+'\n',encoding='utf-8')
script=(r/'output/Flash-CompatV135.ps1').read_text(encoding='utf-8-sig')
script=script.replace('v135','v136').replace('bootcontrol-v136-verification','bluetooth-v136-verification').replace('preserved_v134_entries','preserved_v135_entries')
(r/'output/Flash-CompatV136.ps1').write_text(script,encoding='utf-8-sig')
print(json.dumps(v,indent=2))
