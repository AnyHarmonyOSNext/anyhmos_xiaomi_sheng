# 上游、来源与许可证 / Provenance and licenses

这是多来源研发快照。原有版权和 SPDX 标头予以保留；本包没有替所有文件指定一个统一新许可证。各文件及上游许可证应分别阅读。项目自有且没有授权标头的新增文件，整体开放许可尚待维护者选定，不能据此假定任意再许可。

This is a mixed-provenance development snapshot. Existing copyright and SPDX notices are retained. No new blanket license is imposed on all files. Newly authored files without a license notice still require the maintainer to choose a project license; their presence does not grant an assumed relicensing permission.

| 来源 / Source | 关系 / Relationship |
| --- | --- |
| [YiKongk/AnyHarmonyOS](https://github.com/YiKongk/AnyHarmonyOS) | 主要参考与部分派生适配来源，实际参考提交 `cb1ce16e71392404ecb56f812380ac18c7085520`。本次导出时参考 checkout 无本地修改。The reference checkout is not this device's finished port. |
| [Android common](https://android.googlesource.com/kernel/common) | GKI 5.15.178 基础提交 `6f2f96be86b93de6ed58a2c46b456fb49734c382`。内核导出/IPC 保留对应 GPL/SPDX，模块与配置需匹配。 |
| OpenHarmony 组件 | HDI、IPC、窗口/显示、系统服务、应用/存储/账户等接口参考及派生源。精确仓库/版本记录在 `external/upstream-sources.json`。 |
| Mesa / Turnip / Zink / libdrm | 图形运行路径和接口适配；本地 Mesa tracked diff 与新增源码单独导出。保留各自上游许可。 |
| Qualcomm 开源 PAL/AGM/QRTR/PD mapper 与蓝牙相关参考 | 用于原机硬件后端/接口适配；具体引用见源标头、依赖清单和 `external/licenses/`。 |
| 小米公开设备驱动参考 | THP、WLAN、音频/显示参考；不得把另一机型配置当作 sheng 的验证结果。 |
| BusyBox | GPL 工具参考和构建说明保留，预编译 BusyBox 不打包。 |
| 原厂 Xiaomi / HarmonyOS donor | 仅作为本地合法取得的闭源输入；提取系统库、固件、应用、完整镜像和 SDK 不随本包再分发。 |

`external/upstream-sources.json` 记录了导出时实际读到的 origin、HEAD、dirty 标志和差异规模。`external/patches/` 保存 tracked diff，`external/overlays/` 保存符合源码规则的 untracked 文件；`external/licenses/` 保留所采集的上游根目录许可原文。不是所有上游源码全文都在本包中。

The upstream manifest records the actual origin, HEAD and worktree status read during export. Tracked diffs and untracked source overlays accompany the pinned revisions. Root license notices were collected separately. Full unchanged upstream repositories, toolchains and proprietary inputs are not bundled.

`compat/` 中存在从原系统提取后修改的配置及针对原库的补丁配方。它们不等于原系统的完整开放源码，也不意味着可以重新授权原厂二进制。发布源码快照与提供可再分发完整固件是两件不同的工作。

The package does not claim ownership of upstream work, affiliation with Xiaomi/Huawei, or stock security equivalence. Attribution is preserved; no account tokens are needed to inspect or build the source snapshot.
