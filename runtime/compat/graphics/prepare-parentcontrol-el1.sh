#!/bin/sh
set -eu
B=/busybox
R=/hmos-root
U=/dev/block/by-name/userdata
P=$R/data/service/el1/public
E=$R/data/service/el2/100/parentcontrol

# 目录属性异常时停止准备，保留现有数据
fail() {
 echo "PARENTCONTROL_PREPARE_ERROR: $*" >&2
 exit 1
}

canonical_directory() {
 [ ! -L "$1" ] && [ -d "$1" ] &&
 [ "$($B readlink -f "$1")" = "$1" ]
}

identity() {
 $B stat -c '%d:%i:%u:%g:%a' "$1"
}

[ "$($B id -u)" = 0 ] || fail uid
$B test -b "$U" || fail userdata-device
real=$($B readlink -f "$U") || fail userdata-path
name=${real##*/}
$B grep -qx PARTNAME=userdata "/sys/class/block/$name/uevent" || fail userdata-name
nums=$($B cat "/sys/class/block/$name/dev") || fail userdata-number
$B awk -v dev="$nums" -v target="$R/data" \
 '$3==dev && $5==target && $6 ~ /(^|,)rw(,|$)/ {for(i=7;i<=NF;i++) if($i=="-" && $(i+1)=="ext4") found=1} END {exit !found}' \
 /proc/self/mountinfo || fail userdata-mount
# 首次激活前尚无用户目录，延后家长控制数据准备
if [ ! -e "$E" ] && [ ! -L "$E" ]; then
 echo PARENTCONTROL_PREPARE_DEFERRED_FIRST_BOOT
 exit 0
fi

for path in "$R" "$R/data" "$R/data/service" "$R/data/service/el1" "$P"; do
 canonical_directory "$path" || fail parent-boundary
 [ "$($B stat -c '%u:%g' "$path")" = 0:0 ] || fail parent-owner
done

# 既有用户级目录仅核对身份，不修改内容或权限
canonical_directory "$E" || fail existing-el2-boundary
[ "$($B stat -c '%u:%g:%a' "$E")" = 7007:7007:711 ] || fail existing-el2-identity
el2_before=$(identity "$E") || fail existing-el2-stat
created=0

# 只创建原配置所需的缺失目录
for relative in parentcontrol parentcontrol/databases parentcontrol/cccs_grs \
 parentcontrol/cccs_grs/config parentcontrol/cccs_grs/router; do
 path=$P/$relative
 if [ -e "$path" ] || [ -L "$path" ]; then
  canonical_directory "$path" || fail existing-el1-boundary
  [ "$($B stat -c '%u:%g:%a' "$path")" = 7007:7007:700 ] || fail existing-el1-identity
  continue
 fi
 $B mkdir -m 0700 "$path" || fail mkdir
 canonical_directory "$path" || fail new-directory-boundary
 inode=$($B stat -c '%d:%i' "$path") || fail new-directory-inode
 $B chown -h 7007:7007 "$path" || fail new-directory-owner
 canonical_directory "$path" || fail new-directory-type
 [ "$($B stat -c '%d:%i' "$path")" = "$inode" ] || fail new-directory-changed
 [ "$($B stat -c '%u:%g:%a' "$path")" = 7007:7007:700 ] || fail new-directory-identity
 created=$((created+1))
done
[ "$(identity "$E")" = "$el2_before" ] || fail existing-el2-changed
echo "PARENTCONTROL_DATA_READY created=$created el2_unchanged=1 policy_writes=0"
