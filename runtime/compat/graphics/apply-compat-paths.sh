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
case "$h" in ce1e10e7164e5abe59435ffa336e66dc6f01fec4d5da43100096120a081ca270\ *) ;; *) echo GPU_INPUT_MISMATCH; exit 43;; esac
/busybox chmod 644 /hmos-root/compat/lib64/libvulkan_freedreno.so
echo COMPAT_LOADER_PATHS_INSTALLED

# Only checked compatibility libraries; no vendor files are changed.
h=$(/busybox sha256sum /graphics/zink-runtime-v126.tar.gz)
case "$h" in a9c48ef88e950ab1f65e0db955120542cabd9f5fe1c40bd9c82c0a89d0e193d1\ *) ;; *) echo ZINK_ARCHIVE_MISMATCH; exit 44;; esac
/busybox gzip -dc /graphics/zink-runtime-v126.tar.gz | /busybox tar -xf - -C /hmos-root/compat/lib64
h=$(/busybox sha256sum /hmos-root/compat/lib64/libEGL_impl.so)
case "$h" in 4e4f60765599ac9d1f61b48f1aace6ae9b71a9be77069b5429fda5a1f6353ed8\ *) ;; *) echo ZINK_LIB_MISMATCH; exit 45;; esac
h=$(/busybox sha256sum /hmos-root/compat/lib64/libGLESv1_CM_impl.so.1)
case "$h" in a9e5c19f128ea64d98afc58b1d1e2197dd95441994ef846815b08f3a72baf12d\ *) ;; *) echo ZINK_LIB_MISMATCH; exit 45;; esac
h=$(/busybox sha256sum /hmos-root/compat/lib64/libGLESv2_impl.so.2)
case "$h" in 34c1ae97b9c1d22d75a917864eb492bda6b433a0039febda3cf912129719c65f\ *) ;; *) echo ZINK_LIB_MISMATCH; exit 45;; esac
h=$(/busybox sha256sum /hmos-root/compat/lib64/libgallium-25.0.1.so)
case "$h" in af831f3bcd8958164447d2fd78e83a80aa04bc2d181da130f522f6f35fb75620\ *) ;; *) echo ZINK_LIB_MISMATCH; exit 45;; esac
echo ZINK_RUNTIME_V126_INSTALLED
