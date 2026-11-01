# GEM-W00 SP12 实验镜像构建记录

2026-11-01：供体为三份国行 FULL OTA。基础包实际版本 `GEM-LGRP3-CHN 207.0.0.111(SP12)`，preload `GEM-W00-PRELOAD 207.0.0.3(C00R3)`，cust `GEM-W00-CUST 207.0.0.111(C00)`，区域 all/cn。不得使用 update.bin 通用头的 OpenHarmony 版本作为商用构建号。

| 归档 | 字节 | SHA-256 |
| --- | ---: | --- |
| update_full_base.zip | 16530827953 | 5f9945a7abc1c6a2b6efec7541bf3656f96056dba9b9640db50e91743b241844 |
| update_full_preload_GEM-W00_all_cn_R3.zip | 2481004094 | a2b0c33e70fdbff3e338f4c17991ec5893e34d967894c143b9ec2a1a60935da4 |
| update_full_cust_GEM-W00_all_cn.zip | 13140 | 4eab9f2797e9b216bb753a25854d44c80a9ce4cbe23467e52a93506a1d44c08d |

`tools/extract_huawei_full_ota.py` 使用 64 位组件大小，流式检查 ZIP CRC 及 update.bin 内全部组件 SHA-256，拒绝差分包、危险路径、长度或哈希不符。只提取白名单组件；供体 bootloader、GPT、boot 和设备固件不进入 sheng 刷机包。未完成华为签名密码学验证，完整性检查与签名验证分别表述。

## 补丁和文件系统

[17 份补丁配方](../patches/donor/gem-w00-111-sp12) 包含逐文件输入/输出哈希、偏移、修改前后字节和迁移证据。指令迁移经过函数、控制流和上下文核对；存在编译变化的 memmgr、Wi-Fi、tether 等条目另作人工复核。它们仍属静态分析，运行验证字段保持 false。

`build_promax_ramdisk.py` 从已知 sheng vendor_boot 提取 ramdisk，按新输入重建补丁，保留内核、DTB、bootconfig 及非白名单 cpio 内容。沙箱 JSON 以精确上下文移植 `/compat` 和不支持的 PID namespace 调整，保留本版 `create-only-on-daemon`、GID 等新增内容。Pro Max hw_defaults 只关闭缺失的 NearLink；preload 路径改为 GEM-W00；已有音频目录用挂载覆盖而不是假设不存在。

新 super 仍为 11 GiB，五个逻辑分区名称和 A/B 元数据结构保持基线方案。system、sys_prod、vendor 为供体原始镜像，vendor_dlkm 保留 sheng 内容。完整 preload、chip_prod、anco_hmos、cust、version 存入新建 userdata，由早期 loop 挂载。preload 和 chip_prod 的改动位于 RAM overlay。具体使用限制见[实验包说明](PROMAX-PACKAGE.md)。

已有 Google Windows mke2fs 的目录导入测试失败，因此构建改用已核对来源的 Cygwin mke2fs 1.47.2；先以真实 2.61 GB preload 做写入/读回测试，再生成最终 ext4。显式选择适合当前内核的 ext4 特性，不依赖本机默认配置。userdata 必须匹配目标物理容量。

Cygwin mke2fs、lpmake、magiskboot 来源为 `ColdWindScholar/MIO-KITCHEN-SOURCE` 的固定提交 `085281a7e76297db06271750bb714a6e09444374`，下载文件经 Git blob SHA-1 和本地 SHA-256 核对。EROFS 工具来自 `sekaiacg/erofs-tools` 的 `v1.8.10-251217`，归档 SHA-256 `b6a24de0cfe49a95283cf306db1d158bdb63850e0687c8a8b0f4c4a540ba35ba` 与发布摘要一致。二进制工具及私有镜像不提交本仓库。

## 本地重建入口

示例假定三个 OTA 已由解包工具验证并提取到 donor/extracted，Python 环境含 pyelftools，tools 下有上述 android-fs、erofs-cygwin 工具和依赖 DLL，Windows 安装 Git Bash、7-Zip。先运行各工具 `--help`，使用自己的绝对路径和实测容量。

```powershell
python tools/build_promax_ramdisk.py --donor D:/HMOS6sp/donors/GEM-W00-111-SP12 --original C:/path/to/working-sheng-package --tools D:/HMOS6sp/tools
python tools/build_promax_images.py --donor D:/HMOS6sp/donors/GEM-W00-111-SP12 --original C:/path/to/working-sheng-package --tools D:/HMOS6sp/tools --output D:/HMOS6sp/release/new-empty-build --work D:/HMOS6sp/work/new-build --userdata-bytes 249497890816
python tools/assemble_promax_package.py --package D:/HMOS6sp/release/new-empty-build --platform-tools D:/platform-tools
python -m unittest discover -s tests -p 'test_*.py' -v
powershell -NoProfile -ExecutionPolicy Bypass -File tests/Test-FlashPreflight.ps1
```

输出 images 目录必须为空；不要用重建覆盖已交付版本。构建工具只写主机文件，不访问平板。`Flash-ProMax.ps1` 默认为离线校验，Inspect 只读检查设备，Flash 在全部校验通过并明确输入清空数据确认后才写入。模拟检查覆盖匹配设备、错误机型、错误容量及损坏镜像，测试替换底层传输，不打开真实设备。

最终离线核对覆盖：LP 几何和元数据 SHA-256、所有槽副本、边界/容量/重叠检查、五个逻辑分区逐字节读回哈希、ext4 内五个供体镜像读回哈希、vendor_boot 容器和 cpio 往返、Shell 与 PowerShell 语法。真机启动与三项重点功能应单独记录结果。

## 首次真机挂载检查

整包写入成功后，实际 ext4 userdata 和完整 preload 已挂载。第二个 loop 绑定暴露了节点编号问题：本机启动参数 `loop.max_part=7`，sysfs 的 loop0/1/2 设备号为 `7:0`、`7:8`、`7:16`，连续次设备号会指向分区节点。节点创建已改为逐项读取 `/sys/class/block/loop*/dev`，不硬编码步长，并排除 loop 分区名。

修正设备节点后，chip_prod、anco_hmos、cust、version 四个实际镜像分别完成只读 loop 挂载和卸载测试；这只验证文件系统与 loop 挂载，不代表其中服务可运行。修正版只需更新 vendor_boot，保留已经写入的 super 与 userdata。

Pro Max SceneBoard 还会请求 SA65984 的 PC/平板模式信息。该能力由 `task_manager_service` 提供，原来的精简启动配置没有导入此服务。新增定义保留供体 UID、GID、能力和权限，仅准备其数据目录，未导入缺失的 Kirin sysfs 操作。

真机日志显示，原供体的常量参数会在约 55 秒提前触发此服务，而它依赖的公共事件服务 SA3299 在本移植的桌面阶段才启动，超过了 60 秒依赖等待窗口。因此已把任务服务的自动触发参数改为 `sheng.debug.start.promaxtask`，由 `sheng.debug.start.screen=true` 的 job 先创建并授权目录，再设置新参数。原供体能力参数仍保留为 true；服务的权限不扩大。配置前后哈希写入私有 payload 报告，实际桌面注册结果须继续验证。

开发过程中若 A 槽尚未通过系统启动成功检查，连续重启会消耗 bootloader 的重试次数；耗尽后可能回到 Fastboot。只在对应镜像仍是当前测试目标时重新 `set_active a` 恢复尝试次数，不提前标记 slot successful。整包刷机脚本已在写入全部成功后执行该激活步骤。

## 已解锁状态的启动成功判据

原解锁工具在确认设备已经解锁时输出 `SCREENLOCK_VERIFIED after=0 already_unlocked=1`，执行实际解锁回调时输出 `SCREENLOCK_VERIFIED after=0 callback=0`。旧 Boot Control 判据只识别后一条，因此会在正常进入向导后仍拒绝标记成功。

原生判据现在识别同一工具的共同“已验证状态为解锁”前缀，启动脚本另作完整行校验，只接受已验证解锁记录的回调分支或 already-unlocked 分支。工具先检查账户锁定/认证状态和原 API 返回值，再确认屏幕状态；回调结果和可选 elapsed 耗时属于诊断字段，回调投递本身不是解锁成功条件。启动 ID、内核、设备、服务完成、截图及原机 HAL 的其他检查均保留。当前预编译适配只修改经过哈希保护的 `.rodata` 中唯一字符串，长度保持不变、不修改指令；对应 C 源码同步修正。热验证时在用户确认进入向导、窗口列表确认首次设置前台后，原机 HAL 返回 `rc=0 slot=0 before=0 after=1`。最终镜像的重启回归应以设备验证报告为准。

## 中国区预置图标资源

初步启动后观察到动态时钟、日历、天气回退为静态图标，预置图标列表为空。日志中的 `initDynamicIconState` 报资源名不存在，实际 `const.cust.config_dir_layer` 仅包含 factory，缺少 `/sys_prod/variant/region_comm/china`；供体中的 12 套图标和 dynamic_icons 文件均仍在。在线设置缺失的 CUST 选择参数、刷新主题服务未恢复图标；派生的资源层参数已经只读，不能据此宣称修复成功。

构建工具在 RAM 中的 `const.ohos.para` 补入与三部分包元数据一致的 GEM-W00、all、cn 软件层选择，不改硬件身份参数；并在已有受哈希保护的 baselayer.cfg 兼容策略中显式加入中国区资源层。重启后应核对实际生效路径、预置图标数量、默认图标资源加载及动态显示。此项不能用一般 Vulkan 缓冲绑定正常来代替验收，也不宣称修复华为专用动画设备或所有应用 GPU 路径。
