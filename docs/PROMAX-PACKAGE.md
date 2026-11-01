# sheng · MatePad Pro Max HarmonyOS 7 SP12 实验包

本包以 GEM-W00 国行供体 `GEM-LGRP3-CHN 207.0.0.111(SP12)` 为基础，配套 preload `207.0.0.3(C00R3)`、cust `207.0.0.111(C00)`。这是开发镜像，已完成初步设置向导启动验证；最终镜像的回归范围以 `reports/device-validation.json`（若已生成）为准，不表示 GPU 全应用兼容、144Hz 或卓易通已经修复。

## 使用范围

仅供已解锁的小米平板 6S Pro（sheng），目标 slot A。已读取的物理 super 容量为 11,811,160,064 字节，userdata 为 249,497,890,816 字节。脚本检查产品、解锁状态、Fastboot 模式、分区容量、文件大小和 SHA-256；容量不符即停止。不要绕过检查用于其他存储规格。

`boot`、`init_boot`、AVB 镜像及 `vendor_dlkm` 沿用已启动的 sheng 包；`vendor_boot` 中移植了 17 组针对本版输入哈希的补丁，保留原内核、DTB 和设备固件。没有包含华为 bootloader、GPT 或华为内核。相关二进制 ABI 尚需真机验证。

## 刷机入口

1. 保留原来已经成功启动的刷机包，确保电脑能识别 Fastboot。
2. 双击 `Verify-Package.bat`，或运行 `powershell -NoProfile -ExecutionPolicy Bypass -File .\Flash-ProMax.ps1 -Mode Verify`，只检查本地文件。
3. 平板进入 bootloader Fastboot 后，可用 `-Mode Inspect` 只读检查设备。
4. 双击 `FlashScript.bat`，或用 `-Mode Flash`。设备检查通过后，必须输入 `ERASE SHENG DATA` 才写入。此操作会清空全部用户数据；任何一步失败即停止。

脚本依次写入 A 槽启动链、super、userdata，擦除旧 metadata，最后才设为 A 槽并重启。不会锁回 bootloader。操作日志保存在 `logs`，可能含序列号，不要直接公开上传。

## 分区和数据格式

保持物理 super 的 11 GiB 容量。system、sys_prod、vendor 为新供体，vendor_dlkm 为 sheng 模块。super 内 preload 只是启动映射占位；完整 preload、chip_prod、anco_hmos、cust、version 镜像保存在新建 ext4 的 `/data/hmos-promax`，早期启动通过只读 loop 挂载，preload 和 chip_prod 另加 RAM overlay 以容纳兼容配置。

**本包的 userdata 包含必需的供体镜像。刷入后单独格式化 /data、恢复出厂设置或删除 `/data/hmos-promax`，可能导致无法启动。发生后需要重新刷入本包 userdata.img，不能只运行 format:ext4。** 不要将此目录当作缓存清理。

未携带约 4.77 GB 的 ai_model，因此不承诺相关 AI 功能。卓易通 HAP、anco_hmos 和供体桥接载荷已包含，但当前兼容启动配置没有启用并验证 Android 后端。保留原来的 120Hz 图形路径；144Hz 模式切换尚未实现。

## 核对结果和局限

三份 OTA ZIP 的 CRC、update.bin 的所有组件 SHA-256 已检查；这属于完整性检查，不等于华为签名已完成密码学验证。super 的 LP 元数据校验和、备份、副本、边界和分区内容读回已核对，userdata 中五个镜像逐一读回哈希一致。vendor_boot 的 cpio 往返、脚本语法、内核与 DTB 保留检查通过。详见 `reports` 和 `PACKAGE.json`。

这些离线检查不能证明可以进入桌面，也不能代替图形、存储、音频、网络及长时间运行回归。首次开机可比原包更慢；是否继续等待要结合串口启动日志判断。

Pro Max 特有的任务管理/模式切换服务已按原权限补入，并延至桌面依赖准备阶段启动。启动成功检查同时支持工具验证的“本来已经解锁”和“收到解锁回调”两种路径。系统完成本次启动检查后，才调用原机 Boot Control HAL 标记成功；不通过伪造日志或提前标记来跳过启动验证。

已补入缺失的中国区主题资源层。若沿用之前测试版本的数据，主题缓存可能需要重新应用一次选定的图标或壁纸；实测预置图标预览及重新应用后的壁纸已恢复。动态图标的实际动效仍以设备验证报告为准。

若要回退，需刷回原工作包的 super 和完整启动链，再按之前已验证的流程将 userdata 格式化为 ext4；仅刷 boot 无法回退供体。回退同样会清空数据。

源码和后续适配位于 https://github.com/INTERINIT/anyhmos_xiaomi_sheng/tree/dev/matepad-promax 。私有供体镜像和原始设备日志不上传仓库。
