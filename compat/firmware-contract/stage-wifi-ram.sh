#!/busybox sh
# Stage untouched official firmware as regular RAM files. Never powers hardware.
set -eu
B=/busybox
F=/compat/firmware
S=/compat/original-firmware
[ "$($B readlink -f /dev/block/by-name/modem_a)" = /dev/block/sde7 ] || exit 30
$B mkdir -p "$S" "$F/kiwi"
if ! $B grep -q ' /compat/original-firmware ' /proc/mounts; then
    $B mount -t vfat -o ro /dev/block/sde7 "$S"
fi
$B grep -q '^/dev/block/sde7 /compat/original-firmware vfat ro,' /proc/mounts || exit 31
[ -f "$S/image/kiwi/amss20.bin" ] || exit 32
echo '6735001fa644bdccd2d4aae4deffaf78e99546318bc8ea404212f08c8f5cb831  /compat/original-firmware/image/kiwi/amss20.bin' | $B sha256sum -c -
# Do not use absolute symlinks across the init-task/chroot mount views.
for src in "$S"/image/kiwi/*; do
    [ -f "$src" ] && [ ! -L "$src" ] || exit 33
    base=${src##*/}
    dst="$F/kiwi/$base"
    $B cp "$src" "$dst.ramcopy"
    original=$($B sha256sum "$src"); original=${original%% *}
    copied=$($B sha256sum "$dst.ramcopy"); copied=${copied%% *}
    [ "$original" = "$copied" ] || exit 34
    $B mv "$dst.ramcopy" "$dst"
done
[ -z "$($B find "$F/kiwi" -type l)" ] || exit 35
echo /compat/firmware > /sys/module/firmware_class/parameters/path
echo WIFI_RAM_FIRMWARE_STAGED=1
