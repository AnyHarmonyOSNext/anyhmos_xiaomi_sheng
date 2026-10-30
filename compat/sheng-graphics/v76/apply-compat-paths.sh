#!/bin/sh
set -e
/busybox mkdir -p /hmos-root/compat/bin /hmos-root/compat/lib64
p=/hmos-root/compat/bin/init
h=$(/busybox sha256sum /hmos-root/system/bin/init)
case "$h" in a2d9c09eb841675c39086d7fb6f8769cc9be13099c50c4ed6e05eb1f59c03372\ *) ;; *) echo init-compat-scan_INPUT_MISMATCH; exit 41;; esac
/busybox cp /hmos-root/system/bin/init "$p.new"
echo ZXRjL3NobmcA | /busybox base64 -d | /busybox dd of="$p.new" bs=1 seek=36827 conv=notrunc
h=$(/busybox sha256sum "$p.new")
case "$h" in 7b5d8d4a6e7d96ed044ff97e66b2380bcf79acbe912061b284c99c3018736f79\ *) ;; *) echo init-compat-scan_OUTPUT_MISMATCH; exit 42;; esac
/busybox chmod 755 "$p.new"
/busybox mv "$p.new" "$p"
p=/hmos-root/compat/lib64/libvulkan.so
h=$(/busybox sha256sum /hmos-root/system/lib64/libvulkan.so)
case "$h" in 3d6aa4145996faf241c5e5a2ba1a9161fffe30101c9f19b5f40da25743a5da2d\ *) ;; *) echo vulkan-compat-search_INPUT_MISMATCH; exit 41;; esac
/busybox cp /hmos-root/system/lib64/libvulkan.so "$p.new"
echo L2NvbXBhdC9ldGMAAAAAAAAAAAAAAAAA | /busybox base64 -d | /busybox dd of="$p.new" bs=1 seek=94581 conv=notrunc
h=$(/busybox sha256sum "$p.new")
case "$h" in 1da47edf2298c34eed6ba625c60be4dcece4c4c3e2bbf2de97cd4e3977a09901\ *) ;; *) echo vulkan-compat-search_OUTPUT_MISMATCH; exit 42;; esac
/busybox chmod 644 "$p.new"
/busybox mv "$p.new" "$p"
/busybox gzip -dc /graphics/libvulkan_freedreno.so.gz > /hmos-root/compat/lib64/libvulkan_freedreno.so
h=$(/busybox sha256sum /hmos-root/compat/lib64/libvulkan_freedreno.so)
case "$h" in ad70f97f37dfc511e999f4dcbe8a249ca06a9cb24869e09c6284a64729845955\ *) ;; *) echo GPU_INPUT_MISMATCH; exit 43;; esac
/busybox chmod 644 /hmos-root/compat/lib64/libvulkan_freedreno.so
echo COMPAT_LOADER_PATHS_INSTALLED
