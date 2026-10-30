# 模块与版本入口 / Component and version map

目录版本是试验快照，不是全部应加载的插件。Directories preserve development rounds; existence does not imply acceptance or enablement.

| 模块 / Component | 源码/配方入口 / Entry points | 状态说明 / Notes |
| --- | --- | --- |
| 内核导出与 IPC | `compat/kernel-sheng-exports/`, `compat/sheng-hmos-ipc/`, `external/custom/sheng-hmos-ipc*`, `analysis/gki-sheng-exports.patch`, `tools/prepare_sheng_ipc.py` | 从记录的 Android common 与 AnyHarmonyOS 输入适配；保留上游 SPDX。Some old embedded READMEs describe candidate status at the time, not today's full project status. |
| 图形原生端口 | `external/custom/sheng-graphics-port/`, `compat/sheng-graphics/`, `tools/build_framepacing_v1.py` | 120Hz 基线；历史 GPU 调频不作为当前默认。 |
| 当前熄屏修复 | `compat/sheng-power/screen-v145/`, `tools/build_screen_power_v145.py`, `tools/native_display_wake_v2.cpp`, `tools/build_vendor_screen_power_v145.py` | 已持久刷入，用户实测确认熄屏正常；深睡/长期循环待验。Flashed; screen-off accepted by the user, extended standby tests pending. |
| WebView | `compat/sheng-framework/web-namespace-v143/`, `compat/sheng-graphics/egl-*-v144/`, `tools/build_egl_*v144.py` | renderer namespace 已改，真实网页仍白屏；v144 为实验。 |
| 媒体/allocator | `tools/build_*v127.py` 至 `tools/build_*v130.py`、对应图形目录 | 软件路径、YUV/RGB metadata/alpha/crop；不等于硬解。 |
| 触控 | `compat/sheng-touch/`, `tools/build_input_latency_monitor.py` | THP→MMI；采样/全链路延迟仍需测。 |
| 输入与框架延迟 | `compat/sheng-framework/msdp-local-v1/`, `tools/prepare_msdp_local_v1.py` | 避免可选分布式初始化阻塞本地调用；没有实现跨设备功能。 |
| 存储与账户 | `compat/sheng-framework/storage-local-v1/`, `account-hmac-v1/`, `useriam-v1/`, `external/custom/sheng-useriam-port/` | 真实账户/存储解锁接入；不提供原厂 TEE 安全等价性。 |
| 音频 | `compat/sheng-audio/pal-bridge-v1/`, `pal-lifecycle-v1/`, `lifecycle-v142/`, `tools/build_audio_lifecycle_v142.py` | PAL/AGM 原后端，扬声器播放/暂停恢复已验，完整音频路由未验。 |
| 电池 | `compat/sheng-power/battery-v131/`, `tools/native_battery_*v131.*`, `tools/build_vendor_battery_v131.py` | 原 HDI、服务与公开 NDK 对照验证。 |
| Wi-Fi | `compat/sheng-wireless/`, `tools/*wifi*v134*` | 连接与 Wi-Fi 6 显示已验，Wi-Fi 7 实链/稳定性未验。 |
| 蓝牙 | `compat/sheng-bluetooth/`, `tools/*bluetooth*v136*` 至 `*v139*`, `tools/build_vendor_nearlink_v141.py` | 原硬件路径和设置扫描/开关已有验证，配对/蓝牙音频待验。 |
| 启动布局 | `tools/vendor_payload_entry_v118.c`, `tools/build_vendor_migration_v118.py`, `tools/vendor_ramdisk_edit.py` | 最小 init_boot + vendor_boot 载荷。 |
| 启动成功门槛 | `compat/sheng-bootcontrol/v135/`, `tools/mark-boot-success-v135.sh` | 真实桌面/解锁门槛后使用原 HAL，不是完整 OTA。 |
| USB probe | `tools/hmos_probe_v121.c`、所包含的 `.inc`、`output/Probe-Protocol.ps1` | 部分 include 保留旧版本名；按源码 include 关系构建，不按文件名猜运行版本。 |
| 启动流程 | `compat/sheng-startup/`, `compat/sheng-framework/web-namespace-v143/start-native-desktop-v116.sh` | 文件名 v116 延续使用不表示当前镜像是 v116。 |

`tools/archive/`、旧版本目录、DSC/GPU 策略等保留供审查和复现失败，不应自动启用。没有包含原厂二进制或编译产物；某些历史构建报告里的文件路径只描述当时本地输入，不代表发布包附有该文件。

Historical reports may name binaries that are intentionally excluded. A module having source code is not evidence that it is deployed, supported, secure or functionally complete.
