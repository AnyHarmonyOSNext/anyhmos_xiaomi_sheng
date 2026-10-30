#!/busybox sh
# Stage exact read-only original ADSP firmware in RAM. This does not boot DSPs.
set -eu
B=/busybox
S=/compat/original-firmware
F=/compat/firmware
[ "$($B uname -r)" = 5.15.178-android13-8-00021-g6f2f96be86b9-ab13729987 ] || exit 30
$B grep -q '^/dev/block/sde7 /compat/original-firmware vfat ro,' /proc/mounts || exit 31
[ -f "$S/image/adsp.mdt" ] && [ -f "$S/image/adsp_dtb.mdt" ] || exit 32
count=0
for src in "$S"/image/adsp.* "$S"/image/adsp_dtb.*; do
    [ -f "$src" ] && [ ! -L "$src" ] || exit 33
    name=${src##*/}
    $B cp "$src" "$F/$name.audio-tmp"
    a=$($B sha256sum "$src"); a=${a%% *}
    b=$($B sha256sum "$F/$name.audio-tmp"); b=${b%% *}
    [ "$a" = "$b" ] || exit 34
    $B mv "$F/$name.audio-tmp" "$F/$name"
    echo "AUDIO_FIRMWARE $a $name"
    count=$((count+1))
done
[ "$($B cat /sys/module/firmware_class/parameters/path)" = /compat/firmware ] || exit 35
echo AUDIO_ADSP_RAM_FIRMWARE_STAGED_COUNT=$count
