#!/bin/bash
set -euo pipefail
export PATH="/root/hmos-work/clang-prebuilt/clang-r450784e/bin:$PATH"
export KBUILD_BUILD_USER=build-user
export KBUILD_BUILD_HOST=build-host
module_dir=/root/hmos-work/sheng-display-dsc
workspace='/mnt/c/SHENG_WORKSPACE'
variant="${1:-fix-v2}"
case "$variant" in observe-v1|fix-v2) ;; *) exit 2 ;; esac
source_dir="$workspace/compat/sheng-display-dsc/src"
if [ "$variant" = observe-v1 ]; then source_dir="$workspace/compat/sheng-display-dsc/observe-v1"; fi
mkdir -p "$module_dir"
cp "$source_dir/Makefile" "$module_dir/Makefile"
cp "$source_dir/sheng_dsc_probe.c" "$module_dir/sheng_dsc_probe.c"
make -C /root/hmos-work/gki-5.15.178 \
  O=/root/hmos-work/gki-out-stock ARCH=arm64 LLVM=1 LLVM_IAS=1 \
  CROSS_COMPILE=aarch64-linux-gnu- KCFLAGS=-D__ANDROID_COMMON_KERNEL__ \
  BUILD_NUMBER=13729987 M="$module_dir" -j4 modules
mkdir -p "$workspace/compat/sheng-display-dsc/$variant"
aarch64-linux-gnu-objcopy --strip-debug --remove-section=.BTF --remove-section=.BTF.ext \
  "$module_dir/sheng_dsc_probe.ko" "$workspace/compat/sheng-display-dsc/$variant/sheng_dsc_probe.ko"
