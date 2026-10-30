#!/bin/sh
# Apply only to the Probe's existing RAM overlay. Never modify an image/partition.
set -e
/busybox grep -q ' /hmos-root overlay ' /proc/mounts
/busybox grep -q ' /hmos-ram tmpfs ' /proc/mounts
p=/hmos-root/system/lib64/librender_service_base.z.so
h=$(/busybox sha256sum "$p")
echo "BEFORE $h"
case "$h" in
  0a699e2317dab4699117a90e7e21d5727bd823e3474a70ebaed4d32667e519ff*) ;;
  14ebe64529fe31bba13b65e59d5af27588466b80147a977ae8a28d079c4c9351*) echo ALREADY_INSTALLED; exit 0;;
  *) echo INPUT_MISMATCH; exit 41;;
esac
# New inode: do not mutate the DSO already mapped by the running server.
/busybox cp "$p" "$p.sheng-sync-new"
echo AQCAUg== | /busybox base64 -d | /busybox dd of="$p.sheng-sync-new" bs=1 seek=9029528 conv=notrunc
h=$(/busybox sha256sum "$p.sheng-sync-new")
echo "AFTER $h"
case "$h" in
  14ebe64529fe31bba13b65e59d5af27588466b80147a977ae8a28d079c4c9351*) ;;
  *) echo OUTPUT_MISMATCH; exit 42;;
esac
/busybox chmod 644 "$p.sheng-sync-new"
/busybox mv "$p.sheng-sync-new" "$p"
echo CLIENT_CALLBACK_SYNC_INSTALLED
