#!/bin/sh
set -eu
B=/busybox
R=/hmos-root
U=/dev/block/by-name/userdata
fail() { echo "HMOS_USERDATA_ERROR: $*" >&2; exit 61; }
$B test -b "$U"
real=$($B readlink -f "$U")
name=${real##*/}
$B grep -qx PARTNAME=userdata "/sys/class/block/$name/uevent"
sectors=$($B cat "/sys/class/block/$name/size")
case "$sectors" in ''|*[!0-9]*) fail 'invalid partition size';; esac
$B test "$sectors" -gt 0
nums=$($B cat "/sys/class/block/$name/dev")
# Reject any pre-existing mount of this partition in the bootstrap namespace.
if $B awk -v dev="$nums" '$3==dev {found=1} END {exit !found}' /proc/self/mountinfo; then
 echo HMOS_USERDATA_ALREADY_MOUNTED; exit 60
fi
identity=$($B blkid "$U") || fail 'no filesystem detected; format userdata as ext4 in Recovery'
echo "$identity" | $B grep -Eq '(^|[[:space:]])TYPE="ext4"([[:space:]]|$)' ||
 fail 'userdata must be ext4; automatic formatting is disabled'
# Formatting normally creates a new UUID. Neither an old UUID nor a project
# marker is required: the partition identity and the actual mount are checked.
$B umount "$R/data"
$B mount -t ext4 -o rw,nosuid,nodev,noatime "$U" "$R/data" || fail 'ext4 mount failed'
if ! $B awk -v dev="$nums" -v target="$R/data" \
 '$3==dev && $5==target && $6 ~ /(^|,)rw(,|$)/ {for(i=7;i<=NF;i++) if($i=="-" && $(i+1)=="ext4") found=1} END {exit !found}' /proc/self/mountinfo; then
 $B umount "$R/data"
 fail 'mounted filesystem does not match userdata'
fi
$B chown 0:0 "$R/data"
$B chmod 0771 "$R/data"
$B mknod "$R/dev/block/userdata" b "${nums%:*}" "${nums#*:}"
$B chmod 0600 "$R/dev/block/userdata"
$B ln -s /dev/block/userdata "$R/dev/block/by-name/userdata"
echo "HMOS_DIRECT_USERDATA_EXT4_READY device=$real sectors=$sectors"
$B grep " $R/data " /proc/mounts
$B df -k "$R/data"

# Singleton settingsdata can request its EL2 cache while running as user 0.
$B mkdir -p "$R/data/app/el2/0/base/com.ohos.settingsdata/cache"
$B chmod 0711 "$R/data/app/el2/0" "$R/data/app/el2/0/base"
$B chown 20001:20001 "$R/data/app/el2/0/base/com.ohos.settingsdata" "$R/data/app/el2/0/base/com.ohos.settingsdata/cache"
$B chmod 0700 "$R/data/app/el2/0/base/com.ohos.settingsdata" "$R/data/app/el2/0/base/com.ohos.settingsdata/cache"
echo HMOS_FRESH_SETTINGS_SINGLETON_CACHE_READY
