#!/busybox sh
# Native StorageDaemon fallback for a kernel without HMDFS. No auth bypass.
set -eu
B=/busybox
R=/hmos-root
SRC=$R/system/etc/param/distributed_file.para
DST=$R/compat/etc/distributed_file.para
$B test -f "$SRC"
$B test "$($B grep -c '^const.distributed_file_property.enabled=true$' "$SRC")" = 1
if $B grep -qw hmdfs /proc/filesystems; then
 echo STORAGE_LOCAL_REJECT_KERNEL_HAS_HMDFS
 exit 2
fi
$B mkdir -p "$R/compat/etc"
$B sed 's/^const.distributed_file_property.enabled=true$/const.distributed_file_property.enabled=false/' "$SRC" > "$DST"
$B chmod 0644 "$DST"
$B grep -qx 'const.distributed_file_property.enabled=false' "$DST"
$B mount --bind "$DST" "$SRC"
# Original user-path resolver creates children with non-recursive mkdir.
$B test ! -L "$R/storage/media"
$B mkdir -p "$R/storage/media"
$B chown 0:0 "$R/storage/media"
$B chmod 0711 "$R/storage/media"
echo STORAGE_LOCAL_NATIVE_FALLBACK_READY_PARAMETER_FALSE_MEDIA_PARENT_PRESENT
