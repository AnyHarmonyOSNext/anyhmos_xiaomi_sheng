"""Persist a gated original-device Boot Control HAL call after verified desktop."""
from pathlib import Path
import json
import subprocess
from vendor_ramdisk_edit import edit,sha

r=Path(__file__).resolve().parent.parent
prefix='sheng-compat-v118/'
folder=r/'compat/sheng-bootcontrol/v135'
files=['bootctrl.xiaomi_sm8550.so','libz.so','libsheng_bootcontrol_readonly_v135.so','libsheng_bootcontrol_guarded_v135.so']
hashes={name:sha((folder/name).read_bytes()) for name in files}
assert hashes['bootctrl.xiaomi_sm8550.so']=='a8180cca581f5bd0afdacc215ce29db785d971544e05d9e200872db63bb2d7e1'
assert hashes['libsheng_bootcontrol_guarded_v135.so']=='92db6e9f567ba53854d5dd84b2143ce6f65fca9b9b7555d5b5fc39a4b8dc5430'
names={prefix+'bootcontrol-v135/'+name:(folder/name).read_bytes() for name in files}
names[prefix+'bootcontrol-v135/SHA256SUMS']=''.join(hashes[n]+'  '+n+'\n' for n in files).encode()
names[prefix+'graphics/mark-boot-success-v135.sh']=(r/'tools/mark-boot-success-v135.sh').read_bytes()
applyname=prefix+'graphics/apply-hardware-v116.sh'
startupname=prefix+'graphics/start-native-desktop-v116.sh'
allowed=set(names)|{applyname,startupname,prefix+'MANIFEST.json'}
manifest={}

def syntax(path):
    wsl='/mnt/c/'+str(path).replace('\\','/').split(':/',1)[1]
    subprocess.run(['wsl.exe','--','bash','-n',wsl],check=True,capture_output=True)

def mutate(entries):
    fields=entries[prefix+'graphics/native_brightness_launcher'][0].copy()
    inode=max(f[0] for f,b in entries.values())
    # Every directory and file has its own inode; no accidental hard links.
    dirname=prefix+'bootcontrol-v135'
    dirfields=entries[prefix+'graphics'][0].copy()
    nonlocal_dirs={dirname}
    assert dirname not in entries
    dirfields[0]=inode+1;dirfields[1]=0o40755;inode+=1
    entries[dirname]=(dirfields,b'')
    for name,data in names.items():
        f=fields.copy();inode+=1;f[0]=inode
        f[1]=0o100755 if name.endswith('.sh') else 0o100644
        entries[name]=(f,data)
    f,blob=entries[applyname]
    text=blob.decode()+'''
# Keep Boot Control isolated from the original vendor and the HMOS linker.
$B mkdir -p /compat/bootcontrol-v135
$B cp /sheng-compat-v118/bootcontrol-v135/* /compat/bootcontrol-v135/
$B chmod 0644 /compat/bootcontrol-v135/*
'''
    path=folder/'apply-hardware-v116.sh';path.write_text(text,encoding='utf-8',newline='\n');syntax(path)
    entries[applyname]=(f.copy(),text.encode())
    f,blob=entries[startupname];text=blob.decode()
    original='''trap 'code=$?; $B chroot "$R" /system/bin/param set sheng.debug.start.bootanim false >/dev/null 2>&1 || :; echo "AUTOSTART_EXIT code=$code stage=$stage"; exit "$code"' EXIT'''
    assert text.count(original)==1
    replacement='''autostart_exit() {
 code=$?
 $B chroot "$R" /system/bin/param set sheng.debug.start.bootanim false >/dev/null 2>&1 || :
 echo "AUTOSTART_EXIT code=$code stage=$stage"
 if [ "$code" -eq 0 ] && [ "$stage" = complete ]; then
  if $B sh /graphics/mark-boot-success-v135.sh "$boot_id" > "$R/data/local/tmp/sheng-boot-success-v135.txt" 2>&1; then
   echo AUTOSTART_ORIGINAL_BOOTCONTROL_SUCCESS=1
  else
   mark_code=$?
   echo "AUTOSTART_BOOTCONTROL_NOT_MARKED code=$mark_code"
  fi
 fi
 exit "$code"
}
trap autostart_exit EXIT'''
    text=text.replace(original,replacement)
    path=folder/'start-native-desktop-v116.sh';path.write_text(text,encoding='utf-8',newline='\n');syntax(path)
    entries[startupname]=(f.copy(),text.encode())
    manifest.update({n[len(prefix):]:dict(bytes=len(b),mode=oct(f[1]),sha256=sha(b))
                     for n,(f,b) in entries.items() if n.startswith(prefix) and n!=prefix+'MANIFEST.json'})
    name=prefix+'MANIFEST.json';f,_=entries[name]
    entries[name]=(f.copy(),(json.dumps(manifest,indent=2)+'\n').encode())

dirname=prefix+'bootcontrol-v135'
allowed.add(dirname)
syntax(r/'tools/mark-boot-success-v135.sh')
image=edit(r/'output/vendor_boot_hmos_compat_v134.img',
    'eae74493e4602620c22424bd7a7e2248fec25d5bb7da1d2c92115c9d8b8b084c',
    r/'work/bootcontrol-v135',mutate,allowed,added=set(names)|{dirname})
out=r/'output/vendor_boot_hmos_compat_v135.img';out.write_bytes(image)
v=dict(version='v135',status='built_not_flashed',vendor_boot=dict(file=out.name,bytes=len(image),sha256=sha(image)),
    cpio_verified=True,preserved_v134_entries=True,changed_entries=sorted(allowed),init_boot_unchanged=True,
    dtb_unchanged=True,bootconfig_unchanged=True,stock_vendor_modules_and_audio_unchanged=True,
    usb_v121_unchanged=True,wifi_v134_unchanged=True,original_gpu_governor_unchanged=True,
    original_device_hal=True,guarded_original_hal_hot_verified=True,
    manual_raw_misc_or_gpt_writes=False,post_mark_gpt_crc_and_diff_verified=True,
    hot_mark_evidence='output/logs/command-shell-20261030-115759-bf569e305bba.log',
    gpt_diff_evidence='analysis/gpt-v135-original-hal-diff.json',
    cold_boot_automatic_mark_verified=False,ordinary_reboot_successful_slot_verified=False)
(r/'analysis/bootcontrol-v135-verification.json').write_text(json.dumps(v,indent=2)+'\n',encoding='utf-8')
(r/'output/v135-payload-manifest.json').write_text(json.dumps(manifest,indent=2)+'\n',encoding='utf-8')
script=(r/'output/Flash-CompatV134.ps1').read_text(encoding='utf-8-sig')
script=script.replace('v134','v135').replace('wifi-category-v135-verification','bootcontrol-v135-verification').replace('preserved_v132_entries','preserved_v134_entries')
(r/'output/Flash-CompatV135.ps1').write_text(script,encoding='utf-8-sig')
print(json.dumps(v,indent=2))
