#!/bin/sh
set -eu
B=/busybox
R=/hmos-root
S=/sheng-persistent
U=/dev/block/by-name/userdata
ID=76fb5f0c-a521-4461-948d-60f2204655dc
$B test -b "$U"
$B mkdir -p "$S"
$B mount -t f2fs -o ro,norecovery,nosuid,nodev,noatime "$U" "$S"
$B grep -qx sheng-hmos-data-v1 "$S/hmos-compat/identity"
$B grep -qx "$ID" "$S/hmos-compat/identity"
$B test -f "$S/hmos-compat/data-v1.ext4"
$B test ! -L "$S/hmos-compat/data-v1.ext4"
$B test "$($B stat -c %s "$S/hmos-compat/data-v1.ext4")" = 8589934592
$B umount "$S"
$B mount -t f2fs -o nosuid,nodev,noatime "$U" "$S"
P="$S/hmos-compat/data-v1.ext4"
$B test ! -e /sys/class/block/loop7/loop/backing_file
nums=$($B cat /sys/class/block/loop7/dev)
if [ ! -b /dev/loop7 ]; then $B mknod /dev/loop7 b "${nums%:*}" "${nums#*:}"; fi
$B losetup /dev/loop7 "$P"
$B umount "$R/data"
$B mount -t ext4 -o nosuid,nodev,noatime /dev/loop7 "$R/data"
$B chmod 0771 "$R/data"
echo HMOS_PERSISTENT_EXT4_DATA_READY_UUID_$ID
$B grep " $R/data " /proc/mounts

# Singleton settingsdata can request its EL2 cache while running as user 0.
$B mkdir -p "$R/data/app/el2/0/base/com.ohos.settingsdata/cache"
$B chmod 0711 "$R/data/app/el2/0" "$R/data/app/el2/0/base"
$B chown 20001:20001 "$R/data/app/el2/0/base/com.ohos.settingsdata" "$R/data/app/el2/0/base/com.ohos.settingsdata/cache"
$B chmod 0700 "$R/data/app/el2/0/base/com.ohos.settingsdata" "$R/data/app/el2/0/base/com.ohos.settingsdata/cache"
echo HMOS_SETTINGS_SINGLETON_CACHE_READY
