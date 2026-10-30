#!/bin/sh
set -eu
B=/busybox
R=/hmos-root
P="$R/compat/framework-data.ext4"
$B grep -q ' /hmos-ram tmpfs ' /proc/mounts
$B grep -q ' /hmos-root overlay ' /proc/mounts
$B test ! -e "$P"
$B mkdir -p "$R/compat"
$B truncate -s 1536M "$P"
$B chroot "$R" /system/bin/mke2fs -q -F -t ext4 -O verity,^orphan_file -E lazy_itable_init=0,lazy_journal_init=0 /compat/framework-data.ext4
$B test ! -e /sys/class/block/loop7/loop/backing_file
nums=$($B cat /sys/class/block/loop7/dev)
if [ ! -b /dev/loop7 ]; then $B mknod /dev/loop7 b "${nums%:*}" "${nums#*:}"; fi
$B losetup /dev/loop7 "$P"
$B umount "$R/data"
$B mount -t ext4 -o nosuid,nodev,noatime /dev/loop7 "$R/data"
$B chmod 0771 "$R/data"
echo HMOS_RAM_EXT4_DATA_READY_NO_PHYSICAL_USERDATA
$B grep " $R/data " /proc/mounts
