#!/busybox sh
# The validated v78 startup order, executed on-device without a host command.
set -eu
B=/busybox
R=/hmos-root
stage=prepare
now() { read seconds rest < /proc/uptime; echo "${seconds%.*}"; }
trap 'code=$?; echo "AUTOSTART_EXIT code=$code stage=$stage"; exit "$code"' EXIT
echo AUTOSTART_BEGIN_VERSION=v110
boot_id=$($B cat /proc/sys/kernel/random/boot_id)
$B cat /proc/sys/kernel/random/boot_id /proc/uptime
$B grep -q '^sheng_hmos_ipc ' /proc/modules
stage=hilog
i=0
while ! $B test -S "$R/dev/unix/socket/hilogInput"; do
 i=$((i+1)); [ "$i" -lt 40 ] || exit 21; $B sleep 1
done
stage=core
for gate in coredeps storaged; do $B chroot "$R" /system/bin/param set sheng.debug.start.$gate true; done
$B sleep 2
stage=memmgr
$B chroot "$R" /system/bin/param set sheng.debug.start.memmgr true
deadline=$(($(now)+12))
while ! $B timeout 3 $B chroot "$R" /compat/bin/native_sa_check 1909; do
 if [ "$(now)" -ge "$deadline" ]; then echo MEMMGR_NOT_READY=1; break; fi
 $B sleep 1
done
stage=core
result=$($B timeout 15 $B chroot "$R" /system/bin/sdc filecrypt init_main_user)
echo "$result"
echo "$result" | $B grep -q 'ret: 0'
for gate in storage kvdata useriam account appspawn theme wallpaper ui; do
 $B chroot "$R" /system/bin/param set sheng.debug.start.$gate true
done
$B setsid $B timeout 900 $B chroot "$R" /system/bin/hilog -L I,W,E,F > "$R/data/local/tmp/v110-live.txt" 2>&1 </dev/null &
stage=diagnostics
$B chroot "$R" /system/bin/param set sheng.debug.start.diagnostics true
stage=database
deadline=$(($(now)+90))
i=0
while ! $B timeout 3 $B chroot "$R" /data/local/tmp/native_sa_dump 1301 "/data/local/tmp/v110-database-$boot_id-$i.txt" -l; do
 i=$((i+1)); [ "$(now)" -lt "$deadline" ] || exit 22; $B sleep 1
done
echo AUTOSTART_DATABASE_READY
stage=time
$B chroot "$R" /system/bin/param set sheng.debug.start.time true
deadline=$(($(now)+15))
while ! $B timeout 3 $B chroot "$R" /compat/bin/native_sa_check 3702; do
 if [ "$(now)" -ge "$deadline" ]; then echo TIME_SERVICE_NOT_READY=1; break; fi
 $B sleep 1
done
stage=framework
$B chroot "$R" /system/bin/param set sheng.debug.start.framework true
for id in 1602 404 3706; do
 deadline=$(($(now)+8))
 while ! $B timeout 3 $B chroot "$R" /compat/bin/native_sa_check "$id"; do
  if [ "$(now)" -ge "$deadline" ]; then echo "FRAMEWORK_PROVIDER_NOT_READY=$id"; break; fi
  $B sleep 1
 done
done
stage=media
$B chroot "$R" /system/bin/param set sheng.debug.start.media true
deadline=$(($(now)+40))
while ! $B timeout 3 $B chroot "$R" /compat/bin/native_sa_check 3002; do
 [ "$(now)" -lt "$deadline" ] || exit 35
 $B sleep 1
done
echo AUTOSTART_ORIGINAL_MEDIA_SA3002_READY
stage=codec
$B chroot "$R" /system/bin/param set sheng.debug.start.codec true
deadline=$(($(now)+20))
while ! $B timeout 3 $B chroot "$R" /compat/bin/native_sa_check 3011; do
 if [ "$(now)" -ge "$deadline" ]; then echo AVCODEC_NOT_READY=1; break; fi
 $B sleep 1
done
# Initialize the real WLAN hosts before UI code can request WiFi SAs.
stage=wireless
if $B timeout 50 $B sh "$R/compat/bin/start-wifi-v110.sh" > "$R/data/local/tmp/v110-wifi-startup.log" 2>&1; then
 echo AUTOSTART_WLAN_REQUESTED=1
else
 echo AUTOSTART_WLAN_REQUEST_FAILED=1
fi
stage=netstack
$B chroot "$R" /system/bin/param set sheng.debug.start.netstack true
for id in 1120 1124 1126 1158 1151; do
 deadline=$(($(now)+15))
 while ! $B timeout 3 $B chroot "$R" /compat/bin/native_sa_check "$id"; do
  if [ "$(now)" -ge "$deadline" ]; then echo "PLATFORM_SA_NOT_READY=$id"; break; fi
  $B sleep 1
 done
done
stage=graphics
$B sh /graphics/start-graphics-v110.sh
stage=hardware
$B chroot "$R" /system/bin/param set sheng.debug.start.hardware true
stage=touch
$B chroot "$R" /system/bin/param set sheng.debug.start.touch true
i=0
while ! $B grep -q THP_INPUT_NODE_READY "$R/data/local/tmp/sheng-thp-service.txt"; do
 i=$((i+1)); [ "$i" -lt 20 ] || exit 31; $B sleep 1
done
$B head -n 4 "$R/data/local/tmp/sheng-thp-service.txt"
$B chroot "$R" /system/bin/param set sheng.debug.start.input true
stage=uideps
$B chroot "$R" /system/bin/param set sheng.debug.start.uideps true
for id in 3701 2902; do
 deadline=$(($(now)+20))
 while ! $B timeout 3 $B chroot "$R" /compat/bin/native_sa_check "$id"; do
  if [ "$(now)" -ge "$deadline" ]; then echo "UI_DEPENDENCY_NOT_READY=$id"; break; fi
  $B sleep 1
 done
done
stage=scene
$B cp "$R/data/local/tmp/foundation-app-core.json" "$R/system/profile/foundation.json"
$B chroot "$R" /system/bin/param set sheng.debug.start.screen true
$B chroot "$R" /system/bin/param set sheng.debug.start.compconfig true
stage=inputmethod
$B chroot "$R" /system/bin/param set sheng.debug.start.ime true
deadline=$(($(now)+25))
while ! $B timeout 3 $B chroot "$R" /compat/bin/native_sa_check 3703; do
 if [ "$(now)" -ge "$deadline" ]; then echo INPUTMETHOD_NOT_READY=1; break; fi
 $B sleep 1
done
stage=scene
deadline=$(($(now)+600))
i=0
while :; do
 path="/data/local/tmp/v110-scene-$boot_id-$i.txt"
 if $B timeout 3 $B chroot "$R" /data/local/tmp/native_sa_dump 4606 "$path" -a &&
    $B grep -qE 'SCBScreenLock|SCBDesktop' "$R$path"; then break; fi
 i=$((i+1)); [ "$(now)" -lt "$deadline" ] || exit 32; $B sleep 1
done
stage=wake
$B chroot "$R" /system/bin/param set sheng.debug.display.wake true
$B sleep 2
stage=unlock
$B chroot "$R" /system/bin/param set sheng.debug.screen.unlock true
i=0
while ! $B grep -q 'SCREENLOCK_VERIFIED after=0' "$R/data/local/tmp/sheng-capture/unlock-request.txt"; do
 i=$((i+1)); [ "$i" -lt 40 ] || exit 33; $B sleep 1
done
$B cat "$R/data/local/tmp/sheng-capture/unlock-request.txt"
stage=capture
# Allow asynchronous icon decoding; this is a native system capture, not a draw test.
$B sleep 20
$B chroot "$R" /system/bin/param set sheng.debug.start.capture true
i=0
while :; do
 state=$($B chroot "$R" /system/bin/param get startup.service.ctl.sheng_snapshot)
 if [ "$state" -eq 5 ] 2>/dev/null && $B test -s "$R/data/local/tmp/sheng-capture/display0.jpeg"; then break; fi
 i=$((i+1)); [ "$i" -lt 20 ] || exit 34; $B sleep 1
done
$B cp "$R/data/local/tmp/sheng-capture/display0.jpeg" "$R/data/local/tmp/v110-autostart-desktop.jpeg"
# SceneBoard, account, unlock and native capture have actually completed.
$B chroot "$R" /system/bin/param set bootevent.boot.completed true
echo AUTOSTART_REAL_BOOT_COMPLETED_EVENT=1
stage=complete
echo AUTOSTART_SERVICES_READY=1
echo 'DESKTOP_CONTENT_AND_PHYSICAL_DISPLAY_REQUIRE_EXTERNAL_VERIFICATION=1'
$B cat /proc/uptime
