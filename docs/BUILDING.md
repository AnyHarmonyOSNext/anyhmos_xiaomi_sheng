# 当前源码构建 / Building the selected sources

源码已按功能收敛，构建直接使用最终文件，不再从 v1、v2 逐轮生成后续源码。当前仍是研发源码，并非完整 ROM 或从零一键刷机工具。

The tree keeps the selected implementation of each component. It does not include proprietary inputs, full upstream repositories or flashable images. v146 device acceptance is documented separately; this is not a claim of byte-for-byte reproducibility for every component.

## 外部输入 / External inputs

- sheng 官方 OS3.0.303.0.WNXCNXM 的匹配内核配置、模块和固件，以及项目使用的 MatePad Air HarmonyOS donor 链接库；自行准备，不随仓库分发。
- Harmony native SDK `6.0.0.47`、AArch64 Linux GCC/strip，以及需要的 Android Bionic/C++ 链接环境。
- `external/upstream-sources.json` 记录的上游源码版本；原有许可位于 `external/licenses/`。
- libdrm 静态库、匹配的生成接口头文件、PAL/OpenSSL 等组件输入。部分接口头已收录。

Within the prepared `super`, only `vendor_dlkm` remains stock Xiaomi. Boot image updates require the matching development baseline. Recovery follows the established procedure of restoring this device's own backed-up boot/vendor_boot/init_boot trio first.

全新安装的数据分区要求及最新挂载修复见 [USERDATA.md](USERDATA.md)。普通 ext4 格式化即可准备文件系统；不需要专用 UUID 或标记，启动程序不会自动格式化。The updated mount logic accepts normally formatted ext4 and never formats automatically; the corresponding image still needs device testing.

## 构建入口 / Build entry points

在 WSL 使用 `tools/build_current.py`。它只编译显式选定的目标，不自动刷写或连接设备。

```sh
python3 tools/build_current.py --list
python3 tools/build_current.py composer allocator display-wake --dry-run
python3 tools/build_current.py composer allocator display-wake
python3 tools/build_current.py audio-vdi audio-loader audio-manager
python3 tools/build_current.py bootstrap init-entry touch touch-launcher wifi-category
```

默认编译输出为 `work/current-build/`，构建命令和产物哈希写入其 `build-report.json`。`--dry-run` 可先检查依赖路径。当前脚本覆盖常用适配目标；未提供目标的源文件仍需按原接口与工具链自行构建，不可据此声称完整 ROM 已能一键重建。

| 环境变量 / Variable | 默认位置 / Default |
| --- | --- |
| `SHENG_DEPS` | `/root/hmos-work/graphics-deps` |
| `SHENG_SDK` | `/root/hmos-work/sdk-6.0.0.47/installed/native` |
| `SHENG_UPSTREAM` | `$SHENG_DEPS/source` |
| `SHENG_DONOR_LINK` | 仓库 `work/donor-hdi-link` |
| `SHENG_STAGE` | `$SHENG_DEPS/stage` |
| `SHENG_BIONIC_LINK` | 仓库 `work/audio-bionic-v1/lib64` |
| `SHENG_PAL_INCLUDE` | `/root/hmos-reference/pal-sm8550-a13/inc` |
| `SHENG_ANDROID_CPP_HEADERS` | `/root/hmos-work/clang-prebuilt/clang-r450784e/include/c++/v1` |
| `SHENG_BT_VENDOR_LINK` | 仓库 `work/donor-bluetooth-v136/vendor/lib64` |

`compat/ipc/Makefile` 对应当前模块，应在匹配内核源码和配置下构建；`external/patches/hmos-work--gki-sheng-exports.patch` 与对应 overlay 配套。保留 CFI、符号版本与产品/输入哈希校验。

Mesa 补丁以记录的 upstream HEAD 为基础，EGL 的 `platform_ohos.c` 使用已部署 v126 源码；Turnip `tu_image.cc` 与 v128 源码快照已比对一致。应用 overlay 后，按 Mesa 自身的构建流程配置 Turnip/Zink。原 v144 EGL 实验不再保留。

UserIAM 使用 `tools/build_useriam.py`，需自行准备 target-compatible OpenSSL 头、4.0/4.1 donor stub 和 HDF host 库。`SHENG_USERIAM_VENDOR_LIBS`、`SHENG_USERIAM_HOST_LIBS`、`SHENG_OPENSSL_INCLUDE` 可指定路径。`compat/useriam/software-backend.patch` 描述当前软件后端所需的上游差异，需审查应用到匹配来源；其 4.0 后端和 4.1 adapter 共同组成当前实现，不应互相删减。

## 配置与补丁 / Runtime and patches

`runtime/` 保留当前 v146 脚本与配置，`patches/donor/` 是由最终已部署库和原始 donor 输入生成的合并修补配方。它们保留全文件输入/输出 SHA-256 和逐段 before/after 校验，可用 `tools/apply_guarded_elf_patch.py` 生成副本。原库不分发。

Some runtime scripts intentionally apply dependent stages during startup. Those stages are part of the current boot path, not independently selectable old versions. Runtime checksum constants identify the accepted binaries; newly rebuilt outputs may differ and require independent packaging checks and device validation. Do not blindly copy build output into a ramdisk or remove guards to force a mismatch through.

## 调试与检查 / Debugging and checks

COM probe 不是 ADB。用 `output/Invoke-ProbeCommand.ps1`、文件传输和截图脚本操作；串口请求必须串行。单请求上限约 60 秒，超时完整回复不等于失联。已有测试机数据不应按旧流程清除。

`tools/verify_sources.py` 校验当前源码清单、语法、链接和本地依赖；`tools/refresh_manifest.py` 只更新哈希清单，不打包、不上传。功能验收仍以 [VERIFICATION.md](VERIFICATION.md) 和双语 README 为准。
