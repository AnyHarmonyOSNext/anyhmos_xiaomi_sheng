#!/bin/sh
set -eu
B=/busybox
R=/hmos-root
p="$R/system/lib64/libcode_sign_utils.z.so"
h=$($B sha256sum "$p")
case "$h" in bbd86eec0b55323d61f6f27a7e3c132f7e7fbcdf3820f723d2db7dee40b0b4a9*) ;; *) echo CODE_SIGN_DONOR_MISMATCH; exit 41;; esac
q="$R/compat/lib64/libcode_sign_utils.z.so"
$B test ! -e "$q"
$B cp /graphics/libcode_sign_utils.z.so "$q"
h=$($B sha256sum "$q")
case "$h" in 4ca57938aa23ed1dd4fd585bd411f12ab9a8540f804afe4c30383fff17071364*) ;; *) echo CODE_SIGN_OUTPUT_MISMATCH; exit 42;; esac
$B chmod 0644 "$q"
echo HMOS_ANYHARMONY_DEVELOPMENT_FSVERITY_COMPAT_NO_KERNEL_INTEGRITY_CLAIM
