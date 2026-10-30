#!/bin/bash
set -euo pipefail
export PATH="/root/hmos-work/clang-prebuilt/clang-r450784e/bin:$PATH"
export KBUILD_BUILD_USER=build-user
export KBUILD_BUILD_HOST=build-host
workspace='/mnt/c/SHENG_WORKSPACE'
module_dir=/root/hmos-work/sheng-firmware-contract
mkdir -p "$module_dir" "$workspace/compat/firmware-contract/bin"
cp "$workspace/compat/firmware-contract/src/Makefile" "$module_dir/Makefile"
cp "$workspace/compat/firmware-contract/src/sheng_fw_contract.c" "$module_dir/sheng_fw_contract.c"
make -C /root/hmos-work/gki-5.15.178 \
  O=/root/hmos-work/gki-out-stock ARCH=arm64 LLVM=1 LLVM_IAS=1 \
  CROSS_COMPILE=aarch64-linux-gnu- KCFLAGS=-D__ANDROID_COMMON_KERNEL__ \
  BUILD_NUMBER=13729987 M="$module_dir" -j4 modules
aarch64-linux-gnu-objcopy --strip-debug --remove-section=.BTF --remove-section=.BTF.ext \
  "$module_dir/sheng_fw_contract.ko" "$workspace/compat/firmware-contract/bin/sheng_fw_contract.ko"
python3 "$workspace/tools/verify_kernel_module.py" \
  compat/firmware-contract/bin/sheng_fw_contract.ko analysis/firmware-contract-module-abi.json
