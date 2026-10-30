#!/bin/bash
set -euo pipefail
# Offline ABI build only. Never called by the flashing scripts.
export PATH="/root/hmos-work/clang-prebuilt/clang-r450784e/bin:$PATH"
export KBUILD_BUILD_USER=build-user
export KBUILD_BUILD_HOST=build-host
exec make -C /root/hmos-work/gki-5.15.178 \
  O=/root/hmos-work/gki-out-stock ARCH=arm64 LLVM=1 LLVM_IAS=1 \
  CROSS_COMPILE=aarch64-linux-gnu- KCFLAGS=-D__ANDROID_COMMON_KERNEL__ \
  BUILD_NUMBER=13729987 -j8 vmlinux
