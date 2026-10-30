#!/bin/sh
set -eu
B=/busybox
R=/hmos-root
U=/dev/block/by-name/userdata
ID=57275cef-3a0e-427c-a22e-66ca7e80b893
SECTORS=1662743272
BYTES=851324555264
$B test -b "$U"
real=$($B readlink -f "$U")
name=${real##*/}
$B grep -qx PARTNAME=userdata "/sys/class/block/$name/uevent"
$B test "$($B cat "/sys/class/block/$name/size")" = "$SECTORS"
nums=$($B cat "/sys/class/block/$name/dev")
# Reject any pre-existing mount of this partition in the bootstrap namespace.
if $B awk -v dev="$nums" '$3==dev {found=1} END {exit !found}' /proc/self/mountinfo; then
 echo HMOS_USERDATA_ALREADY_MOUNTED; exit 60
fi
identity=$($B blkid "$U")
echo "$identity" | $B grep -Fq "UUID=\"$ID\""
echo "$identity" | $B grep -Fq 'TYPE="ext4"'
$B umount "$R/data"
$B mount -t ext4 -o ro,nosuid,nodev,noatime "$U" "$R/data"
expected=$(printf 'sheng-userdata-direct-v1\n%s\n%s' "$ID" "$BYTES")
if [ "$($B cat "$R/data/.sheng-userdata-layout")" != "$expected" ]; then
 $B umount "$R/data"
 echo HMOS_USERDATA_PROVISIONING_MARKER_MISMATCH; exit 61
fi
$B mount -o remount,rw,nosuid,nodev,noatime "$R/data"
$B chown 0:0 "$R/data"
$B chmod 0771 "$R/data"
$B mknod "$R/dev/block/userdata" b "${nums%:*}" "${nums#*:}"
$B chmod 0600 "$R/dev/block/userdata"
$B ln -s /dev/block/userdata "$R/dev/block/by-name/userdata"
echo HMOS_DIRECT_USERDATA_EXT4_READY_UUID_$ID
$B grep " $R/data " /proc/mounts
$B df -k "$R/data"

# Singleton settingsdata can request its EL2 cache while running as user 0.
$B mkdir -p "$R/data/app/el2/0/base/com.ohos.settingsdata/cache"
$B chmod 0711 "$R/data/app/el2/0" "$R/data/app/el2/0/base"
$B chown 20001:20001 "$R/data/app/el2/0/base/com.ohos.settingsdata" "$R/data/app/el2/0/base/com.ohos.settingsdata/cache"
$B chmod 0700 "$R/data/app/el2/0/base/com.ohos.settingsdata" "$R/data/app/el2/0/base/com.ohos.settingsdata/cache"
echo HMOS_FRESH_SETTINGS_SINGLETON_CACHE_READY
