#!/bin/sh
set -e
/busybox grep -q ' /hmos-root overlay ' /proc/mounts
p=/hmos-root/system/bin/bootanimation
h=$(/busybox sha256sum "$p")
case "$h" in f019c8fbf7a263d5e4f0e6440e206bcb40b622964065b75b9da383535ba5910b*) ;; *) echo INPUT_MISMATCH; exit 41;; esac
/busybox cp "$p" "$p.sheng-eof-new"
echo AQAAAAUAAACczAAAAAAAAJzcAAAAAAAAnNwAAAAAAACUXwIAAAAAAJRfAgAAAAAAABAAAAAAAAA= | /busybox base64 -d | /busybox dd of="$p.sheng-eof-new" bs=1 seek=232 conv=notrunc
echo tZn/Fw== | /busybox base64 -d | /busybox dd of="$p.sheng-eof-new" bs=1 seek=157128 conv=notrunc
echo HwAAcWvSDFQAywxUSWYAFA== | /busybox base64 -d | /busybox dd of="$p.sheng-eof-new" bs=1 seek=52380 conv=notrunc
h=$(/busybox sha256sum "$p.sheng-eof-new")
echo "AFTER $h"
case "$h" in 1947fcb520bc5794103c2ef4777a3e0ab225640485d4d7a2c7a8934eb9f3bbd0*) ;; *) echo OUTPUT_MISMATCH; exit 42;; esac
/busybox chmod 755 "$p.sheng-eof-new"
/busybox mv "$p.sheng-eof-new" "$p"
echo BOOTANIMATION_EOF_INSTALLED
