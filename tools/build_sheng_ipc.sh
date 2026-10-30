#!/bin/bash
set -euo pipefail
export PATH="/root/hmos-work/clang-prebuilt/clang-r450784e/bin:$PATH"
export KBUILD_BUILD_USER=build-user
export KBUILD_BUILD_HOST=build-host
if [ ! -f /root/hmos-work/gki-out-stock/scripts/module.lds ]; then
  make -C /root/hmos-work/gki-5.15.178 \
    O=/root/hmos-work/gki-out-stock ARCH=arm64 LLVM=1 LLVM_IAS=1 \
    CROSS_COMPILE=aarch64-linux-gnu- KCFLAGS=-D__ANDROID_COMMON_KERNEL__ \
    BUILD_NUMBER=13729987 modules_prepare
fi
exec make -C /root/hmos-work/gki-5.15.178 \
  O=/root/hmos-work/gki-out-stock ARCH=arm64 LLVM=1 LLVM_IAS=1 \
  CROSS_COMPILE=aarch64-linux-gnu- KCFLAGS=-D__ANDROID_COMMON_KERNEL__ \
  BUILD_NUMBER=13729987 M=/root/hmos-work/sheng-hmos-ipc -j4 "${1:-modules}"
