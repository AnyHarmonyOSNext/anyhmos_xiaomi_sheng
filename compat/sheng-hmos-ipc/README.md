# sheng 5.15 IPC compatibility candidate

Derived from YiKongk/AnyHarmonyOS commit cb1ce16, sm8650/kernel-port/driver-module.
Original GPL-2.0 SPDX headers and Huawei/Google copyrights are retained.
The reference repository is unchanged. No commits or pushes were performed.

The isolated working copy is /root/hmos-work/sheng-hmos-ipc. Reproduce its explicit
API adaptations with tools/prepare_sheng_ipc.py and review
analysis/sheng-ipc-backport.patch. The kernel tree itself has no driver patches.

Built against exact Google common 6f2f96be86b93de6ed58a2c46b456fb49734c382,
the extracted stock 303 configuration and Android clang r450784e / 14.0.7.
2733 observed original vendor-module imports match the rebuilt vmlinux CRCs;
module_layout is 0x0222dd63. This does not establish runtime CFI correctness.

Backports cover register_shrinker, cache header inclusion, the local Binder
extended-error UAPI, close_fd_get_file refcount semantics, the 5.15 freezer
accounting API and VMA flags. No kernel task layout or security checks are replaced.
Device names are isolated hmos_binder/hmos_hwbinder/hmos_vndbinder and access_token_id.

sheng_hmos_ipc.debug.ko retains debug information. sheng_hmos_ipc.ko removes DWARF
and module BTF, whose base type IDs cannot be assumed to match the stock vmlinux.
Both retain CFI and symbol versions. Neither has been validated on the device yet.
Do not load into the TWRP 5.15.144 kernel; only test on the verified 303 kernel.
