#!/busybox sh
# The original device HAL is invoked only after this boot's successful desktop.
set -eu
B=/busybox
R=/hmos-root
D=/compat/bootcontrol-v135
[ "$#" -eq 1 ] || exit 31
[ "$1" = "$($B cat /proc/sys/kernel/random/boot_id)" ] || exit 32
[ "$($B uname -r)" = 5.15.178-android13-8-00021-g6f2f96be86b9-ab13729987 ] || exit 33
$B grep -q '^androidboot.hardware.sku = "sheng"$' /proc/bootconfig
completed=$($B chroot "$R" /system/bin/param get bootevent.boot.completed)
[ "$(echo "$completed" | $B tr -d ' \r\n')" = true ] || exit 34
# 仅接受状态接口确认解锁后产生的完整记录
$B grep -Eq '^SCREENLOCK_VERIFIED after=0 (callback=-?[0-9]+( elapsed=[0-9]+)?|already_unlocked=1)$' \
 "$R/data/local/tmp/v116-autostart.txt" || exit 36
cd "$D"
$B sha256sum -c SHA256SUMS
if [ -e /dev/block/bootdevice ] || [ -L /dev/block/bootdevice ]; then
 [ "$($B readlink -f /dev/block/bootdevice)" = /dev/block ] || exit 35
else
 $B ln -s /dev/block /dev/block/bootdevice
fi
$B timeout 8 $B env LD_LIBRARY_PATH="$D:/compat/audio-runtime/lib64" \
 LD_PRELOAD="$D/libsheng_bootcontrol_guarded_v135.so" SHENG_MARK_SUCCESS_BOOT_ID="$1" \
 /compat/audio-runtime/bin/linker64 /compat/audio-runtime/bin/agmplay -h
