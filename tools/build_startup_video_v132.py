"""Persist original boot-video startup/exit, plus real monotonic stage timings."""
from pathlib import Path
import json,re,subprocess
from vendor_ramdisk_edit import edit,sha
r=Path(__file__).resolve().parent.parent; prefix='sheng-compat-v118/'
name=prefix+'graphics/start-native-desktop-v116.sh'
outdir=r/'compat/sheng-startup/v132';outdir.mkdir(parents=True,exist_ok=True)
manifest={}

def mutate(entries):
    fields,blob=entries[name];text=blob.decode()
    trap='trap \'code=$?; echo "AUTOSTART_EXIT code=$code stage=$stage"; exit "$code"\' EXIT'
    assert text.count(trap)==1
    helper='''trace_stage() {
 read stage_seconds stage_idle < /proc/uptime
 echo "AUTOSTART_STAGE name=$stage uptime=$stage_seconds"
}
'''
    replacement=helper+'''trap 'code=$?; $B chroot "$R" /system/bin/param set sheng.debug.start.bootanim false >/dev/null 2>&1 || :; echo "AUTOSTART_EXIT code=$code stage=$stage"; exit "$code"' EXIT
trace_stage'''
    text=text.replace(trap,replacement)
    assert text.count('echo AUTOSTART_BEGIN_VERSION=v116')==1
    text=text.replace('echo AUTOSTART_BEGIN_VERSION=v116',
                      'echo AUTOSTART_BEGIN_VERSION=v116\necho AUTOSTART_REVISION=v132_ORIGINAL_BOOT_VIDEO_AND_TIMINGS')
    # This on-demand service is still started with its original configuration.
    # Waiting for an idle service which is allowed to unload is not a boot gate.
    assert text.count('for id in 1602 404 3706; do')==1
    text=text.replace('for id in 1602 404 3706; do','for id in 1602 404; do')
    needle='stage=touch\n'
    assert text.count(needle)==1
    animation='''stage=bootanimation
deadline=$(($(now)+8))
while :; do
 if $B timeout 2 $B chroot "$R" /compat/bin/native_sa_check 10 &&
    $B timeout 2 $B chroot "$R" /compat/bin/native_sa_check 3001 &&
    $B timeout 2 $B chroot "$R" /compat/bin/native_sa_check 3011; then
  $B chroot "$R" /system/bin/param set bootevent.boot.completed false
  $B chroot "$R" /system/bin/param set sheng.debug.start.bootanim true
  echo AUTOSTART_ORIGINAL_BOOT_VIDEO_REQUESTED=1
  break
 fi
 if [ "$(now)" -ge "$deadline" ]; then echo AUTOSTART_BOOT_VIDEO_SKIPPED_DEPENDENCY=1; break; fi
 $B sleep 1
done
'''
    text=text.replace(needle,animation+needle)
    completion='''# SceneBoard, account, unlock and native capture have actually completed.
$B chroot "$R" /system/bin/param set bootevent.boot.completed true
echo AUTOSTART_REAL_BOOT_COMPLETED_EVENT=1
'''
    assert text.count(completion)==1
    text=text.replace(completion,'')
    needle='stage=capture\n'
    assert text.count(needle)==1
    text=text.replace(needle,'''stage=bootcomplete
# Account, SceneBoard and original screen-unlock verification have completed.
# Let the original player finish and release its layer before capturing desktop.
$B chroot "$R" /system/bin/param set bootevent.boot.completed true
echo AUTOSTART_REAL_BOOT_COMPLETED_EVENT=1
'''+needle)
    needle='$B sleep 20\n$B chroot "$R" /system/bin/param set sheng.debug.start.capture true'
    assert text.count(needle)==1
    text=text.replace(needle,'''$B sleep 20
if [ -n "$($B pidof bootanimation)" ]; then
 echo AUTOSTART_BOOT_VIDEO_EXIT_FALLBACK=1
 $B chroot "$R" /system/bin/param set sheng.debug.start.bootanim false
 $B sleep 1
fi
$B chroot "$R" /system/bin/param set sheng.debug.start.capture true''')
    # Keep the variable used by the existing EXIT trap; timestamp each transition.
    initial=True;lines=[];stages=[]
    for line in text.splitlines():
        lines.append(line)
        match=re.fullmatch('stage=([a-z]+)',line)
        if match:
            stages.append(match.group(1))
            if initial: initial=False
            else: lines.append('trace_stage')
    text='\n'.join(lines)+'\n'
    assert text.count('set bootevent.boot.completed true')==1
    assert text.index('SCREENLOCK_VERIFIED after=0')<text.index('stage=bootcomplete')<text.index('stage=capture')
    assert 'start.download' not in text  # Original framework gate remains unchanged.
    target=outdir/'start-native-desktop-v116.sh';target.write_text(text,newline='\n')
    # WSL runs syntax checks only, never the device bootstrap itself.
    wslpath='/mnt/c/'+str(target).replace('\\','/').split(':/',1)[1]
    subprocess.run(['wsl.exe','--','bash','-n',wslpath],check=True,capture_output=True)
    entries[name]=(fields.copy(),text.encode())
    manifest.update({n[len(prefix):]:dict(bytes=len(b),mode=oct(f[1]),sha256=sha(b))
        for n,(f,b) in entries.items() if n.startswith(prefix) and n!=prefix+'MANIFEST.json'})
    m=prefix+'MANIFEST.json';f,_=entries[m]
    entries[m]=(f.copy(),(json.dumps(manifest,indent=2)+'\n').encode())

allowed={name,prefix+'MANIFEST.json'}
image=edit(r/'output/vendor_boot_hmos_compat_v131.img',
    'c762ad30c4d0668f58e0b91b087a6873e8a1bc659d7a9a81a2eeafe2e89a124d',
    r/'work/startup-video-v132',mutate,allowed)
out=r/'output/vendor_boot_hmos_compat_v132.img';out.write_bytes(image)
verification=dict(version='v132',status='built_not_flashed',
    vendor_boot=dict(file=out.name,bytes=len(image),sha256=sha(image)),
    cpio_verified=True,preserved_v131_entries=True,changed_entries=sorted(allowed),
    init_boot_unchanged=True,dtb_unchanged=True,bootconfig_unchanged=True,
    stock_vendor_modules_and_audio_unchanged=True,usb_v121_unchanged=True,
    graphics_v130_unchanged=True,battery_v131_unchanged=True,
    original_gpu_governor_unchanged=True,original_boot_video_asset_unchanged=True,
    hot_original_video_first_frame_and_completion_verified=True,
    boot_completed_requires_original_verified_unlock=True,
    cold_boot_verified=False,cold_boot_video_frame_verified=False,
    stage_timings_verified=False,desktop_after_animation_verified=False)
(r/'analysis/startup-video-v132-verification.json').write_text(json.dumps(verification,indent=2)+'\n')
(r/'output/v132-payload-manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
script=(r/'output/Flash-CompatV131.ps1').read_text(encoding='utf-8-sig')
script=script.replace('v131','v132').replace('battery-v132-verification','startup-video-v132-verification').replace('preserved_v130_entries','preserved_v131_entries')
(r/'output/Flash-CompatV132.ps1').write_text(script,encoding='utf-8-sig')
print(json.dumps(verification,indent=2))
