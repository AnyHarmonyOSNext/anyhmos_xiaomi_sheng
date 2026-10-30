#!/bin/sh
set -e
/busybox grep -q ' /hmos-root overlay ' /proc/mounts
p=/hmos-root/system/bin/bootanimation
h=$(/busybox sha256sum "$p")
case "$h" in 1947fcb520bc5794103c2ef4777a3e0ab225640485d4d7a2c7a8934eb9f3bbd0*) ;; *) echo INPUT_MISMATCH; exit 41;; esac
/busybox cp "$p" "$p.sheng-context-new"
echo /9r/Fw== | /busybox base64 -d | /busybox dd of="$p.sheng-context-new" bs=1 seek=90288 conv=notrunc
echo HwUAcUmmBFQgAIBSDyUAFA== | /busybox base64 -d | /busybox dd of="$p.sheng-context-new" bs=1 seek=52396 conv=notrunc
h=$(/busybox sha256sum "$p.sheng-context-new")
echo "AFTER $h"
case "$h" in 769fe9ce99f8b3178be949c9ed9eb0f1224ff582e1dc924f9ea9ec2eb03c6a9e*) ;; *) echo OUTPUT_MISMATCH; exit 42;; esac
/busybox chmod 755 "$p.sheng-context-new"
/busybox mv "$p.sheng-context-new" "$p"
echo BOOTANIMATION_CONTEXT_INSTALLED
