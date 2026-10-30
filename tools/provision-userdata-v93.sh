#!/system/bin/sh
# Explicit one-time destructive initialization; NEVER included in the boot image.
# User requested a clean filesystem and explicitly rejected preserving old data.
set -eu
B=/tmp/busybox
U=/dev/block/by-name/userdata
ID=57275cef-3a0e-427c-a22e-66ca7e80b893
SECTORS=1662743272
BYTES=851324555264
test "$(getprop ro.product.device)" = sheng
test "$(getprop ro.serialno)" = YOUR_DEVICE_SERIAL
test "$(getprop ro.twrp.version)" = 3.7.1_12-0
test -x "$B"
test -b "$U"
real=$($B readlink -f "$U")
name=${real##*/}
$B grep -qx PARTNAME=userdata "/sys/class/block/$name/uevent"
test "$($B cat "/sys/class/block/$name/size")" = "$SECTORS"
nums=$($B cat "/sys/class/block/$name/dev")
test "$nums" = 259:13
echo "PROVISION_IDENTITY serial=YOUR_DEVICE_SERIAL product=sheng target=$real dev=$nums bytes=$BYTES"
if ! $B awk -v dev="$nums" '$3==dev {found=1} END {exit !found}' /proc/self/mountinfo; then
 echo USERDATA_ALREADY_UNMOUNTED
else
 twrp unmount data
fi
if $B awk -v dev="$nums" '$3==dev {found=1} END {exit !found}' /proc/self/mountinfo; then
 echo REFUSE_FORMAT_MOUNTED_USERDATA; exit 71
fi
test ! -e /sys/class/block/loop7/loop/backing_file
# Build an empty filesystem on all of this partition; no old image is copied.
mke2fs -F -t ext4 -b 4096 -I 256 -i 65536 -m 0 -L HMOS_USERDATA -U "$ID" \
 -O has_journal,extent,huge_file,flex_bg,dir_nlink,extra_isize,uninit_bg,verity,^encrypt,^64bit,^metadata_csum \
 -E nodiscard,lazy_itable_init=1,lazy_journal_init=1 "$U"
$B sync
e2fsck -f -n "$U"
identity=$($B blkid "$U")
echo "$identity"
echo "$identity" | $B grep -Fq "UUID=\"$ID\""
echo "$identity" | $B grep -Fq 'TYPE="ext4"'
tune2fs -l "$U"
$B mkdir -p /tmp/hmos-fresh-data
$B mount -t ext4 -o nosuid,nodev,noatime "$U" /tmp/hmos-fresh-data
# A pristine filesystem may have only lost+found before its layout marker.
test "$($B ls -A /tmp/hmos-fresh-data)" = lost+found
printf 'sheng-userdata-direct-v1\n%s\n%s\n' "$ID" "$BYTES" > /tmp/hmos-fresh-data/.sheng-userdata-layout
$B chmod 0600 /tmp/hmos-fresh-data/.sheng-userdata-layout
$B chown 0:0 /tmp/hmos-fresh-data
$B chmod 0771 /tmp/hmos-fresh-data
$B df -k /tmp/hmos-fresh-data
$B ls -lan /tmp/hmos-fresh-data
$B sync
$B umount /tmp/hmos-fresh-data
echo HMOS_WHOLE_USERDATA_FRESH_PROVISIONED_NO_OLD_DATA_RESTORED
