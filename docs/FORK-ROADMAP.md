# MatePad Pro Max 供体与 sheng 后续适配

本分支基于 `AnyHarmonyOSNext/anyhmos_xiaomi_sheng` 的 `5f520ea2096ad1e989ac29f3f06f096b0873c837`。保留原版权、来源及逐文件许可，不给上游代码重新指定整体许可证。现有功能说明属于 MatePad Air 基线；本分支尚未完成 Pro Max 移植，也没有发布新 ROM。

## 当前已验证内容

2026-11-01 在 sheng 真机上仅将 userdata 建为普通 ext4 后重启。读写挂载成功，用户确认进入向导/桌面；后续诊断确认 `bootevent.boot.completed=true`、启动脚本完整结束及原机 bootcontrol 标记成功。此次没有重刷启动分区或 super。

内核枚举了 3048×2032 的 120、144、90、60、50、48、30Hz 模式，GPU 标识为 Adreno740v2。这只证明模式存在，不代表 144Hz 切换、VSync 或各应用 GPU 路径通过验收。公开的脱敏摘要见 [baseline](../analysis/fork-baseline-20261101.json)，原始串口日志保留在本地。

## 工作顺序与完成条件

| 方向 | 当前具体入口 | 完成条件 |
| --- | --- | --- |
| Pro Max 供体 | [获取记录](DONOR-ACQUISITION.md)；先确认国行机型、完整构建号、全量/增量属性、各包哈希及卓易通载荷 | 可提取一致的 system/vendor/sys_prod/相关应用与运行时；重新建立 ABI、依赖及逐库补丁清单；启动、输入、显示、存储、无线、音频回归通过 |
| GPU 各应用 | Mesa Turnip/Zink/EGL、allocator/composer、RenderService；先记录应用和版本及复现场景 | 证明目标应用实际加载目标图形库并提交硬件 GPU 工作；检查格式/modifier、跨进程缓冲共享、alpha、fence 生命周期；冷启动、视频、旋转、分屏、亮灭屏及压力测试无新增损坏 |
| 144Hz | `compat/display/composer_vdi.cpp` 已收集 DRM 模式，但两个 SupportedModes 接口只返回当前模式、GetDisplayMode 固定 0、SetDisplayMode 拒绝其他 ID | 向系统暴露真实模式和稳定 ID；通过 atomic TEST_ONLY 后切换，失败时保留原模式；更新 mode blob、VSync 周期与状态；实测扫描输出和帧间隔，再验收应用帧率、亮灭屏和回退 120Hz |
| 卓易通 | 从供体定位应用、镜像、服务、配置、设备依赖及图形桥接；确定实际采用的容器/虚拟机机制 | 后端启动、有独立且正确的 Android Binder/设备路径；安装和启动测试 APK；GPU/EGL/Vulkan、输入、音频、网络、存储和重启持久化通过；不得用鸿蒙 IPC 节点冒充 Android Binder |

GPU 测试矩阵逐项记录：应用/版本、场景、实际渲染器、硬件工作证据、缓冲格式、同步错误、帧时间分布、截图/日志和持续时间。系统模式 144Hz、应用渲染 144fps、触控采样率是不同指标，分别验收。

当前内核读取到 `CONFIG_PID_NS`、`CONFIG_USER_NS` 未启用，KVM 配置启用但检查路径未发现 `/dev/kvm`。这些是待与真实容器后端对照的条件，不是已验证的根因；不能只凭配置声称虚拟化可用，也不能凭设备节点缺失断言所有容器方案不可行。

## 本分支工具

`output/Collect-PortBaseline.ps1 -Port COM5` 复用现有 probe 协议做只读检查。端口由本机枚举确定，不能把 COM5 写成所有电脑通用值。命令必须串行。原始日志可能夹杂设备日志，仅保存在被忽略的 `output/logs/`；分享前检查和脱敏。该工具不刷写、不切换刷新率、不启动容器。

`tools/audit_donor.py` 为**已解包目录**计算逐文件 SHA-256，记录 ELF 位宽/机器号，并按每个路径分别检查现有 donor patch 的输入哈希。它不解包 OTA、不验证签名、不证明 ABI 兼容，也不修改固件。相同文件名不表示二进制兼容。

```powershell
python tools/audit_donor.py work/donor-promax-extracted --model ACTUAL_MODEL --build ACTUAL_FULL_BUILD --output work/donor-promax-audit.json
python -m unittest discover -s tests -p test_audit_donor.py -v
python tools/refresh_manifest.py
python tools/verify_sources.py
```

当前电脑未就绪的原构建依赖包括 WSL/Linux 构建环境、匹配 native SDK、上游源码、libdrm 及 donor 链接库。本次仅验证工具和真机只读采集，不声称编译或刷测了 144Hz、Pro Max 或卓易通修复。构建准备沿用 [BUILDING.md](BUILDING.md)，不移除已有二进制哈希保护来强行使用新供体。

发布前保留可恢复的原机分区备份、明确镜像来源和哈希；私有系统镜像、应用、设备备份、个人串口日志和凭据不进入 Git。
