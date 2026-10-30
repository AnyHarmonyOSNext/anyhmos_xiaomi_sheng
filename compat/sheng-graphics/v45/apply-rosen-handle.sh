#!/bin/sh
set -e
/busybox grep -q ' /hmos-root overlay ' /proc/mounts
p=/hmos-root/system/lib64/librender_service_base.z.so
h=$(/busybox sha256sum "$p")
case "$h" in 0a699e2317dab4699117a90e7e21d5727bd823e3474a70ebaed4d32667e519ff*) ;; *) echo INPUT_MISMATCH; exit 41;; esac
/busybox cp "$p" "$p.sheng-flag-new"
echo CQCEUg== | /busybox base64 -d | /busybox dd of="$p.sheng-flag-new" bs=1 seek=9157364 conv=notrunc
h=$(/busybox sha256sum "$p.sheng-flag-new")
echo "AFTER $h"
case "$h" in d423413ec1fc58f40c5b04846b00530a4d82d0929eee769ede3bf5c605e5a77d*) ;; *) echo OUTPUT_MISMATCH; exit 42;; esac
/busybox chmod 644 "$p.sheng-flag-new"
/busybox mv "$p.sheng-flag-new" "$p"
echo ROSEN_OHOS_HANDLE_FLAG_INSTALLED
