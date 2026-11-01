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
