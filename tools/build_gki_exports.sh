#!/bin/bash
set -euo pipefail
export PATH="/root/hmos-work/clang-prebuilt/clang-r450784e/bin:$PATH"
export KBUILD_BUILD_USER=sheng-hmos-exports
export KBUILD_BUILD_HOST=local-wsl
export KBUILD_BUILD_VERSION=2
exec make -C /root/hmos-work/gki-sheng-exports \
  O=/root/hmos-work/gki-out-sheng-exports ARCH=arm64 LLVM=1 LLVM_IAS=1 \
  CROSS_COMPILE=aarch64-linux-gnu- KCFLAGS=-D__ANDROID_COMMON_KERNEL__ \
  BUILD_NUMBER=13729987 -j8 Image
