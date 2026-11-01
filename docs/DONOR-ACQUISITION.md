# MatePad Pro Max HarmonyOS 7 供体获取记录

检查日期：2026-11-01。目标是国行 MatePad Pro Max 的 HarmonyOS 7，卓易通按随系统供体获取来调查，不能把应用入口是否存在当作完整 Android 后端已取得。

## 已核对的入口

1. [华为官方 HarmonyOS 7 支持机型](https://consumer.huawei.com/cn/support/harmonyos/models-7/)列出 MatePad Pro Max。[官方版本升级指导](https://consumer.huawei.com/cn/support/content/zh-cn16116389/)提供设备端设置/检查更新及升级尝鲜流程，不是可直接供 PC 下载的机型全量包索引。
2. [国行规格](https://consumer.huawei.com/cn/tablets/matepad-pro-max/specs/)仍列出出厂 HarmonyOS 6.1；必须从实际更新包元数据确认取得的是目标 7.x 构建，不能从产品网页推断当前包版本。
3. [华为云镜像的 7.0 目录](https://mirrors.huaweicloud.com/harmonyos/os/7.0-Release/)可见 SDK、源码和开发板镜像。检查到的列表没有本机型的商用系统全量包，开发板 ROM 不能替代供体。
4. 社区[机型索引](https://github.com/KHwang9883/MobileModels/blob/master/brands/huawei_cn.md)提供 GEM-W00/GEM-W10 等国行候选代码；这是定位线索，最终以包内产品和区域元数据为准，不能混入 GEM-W09 等海外包或相似命名机型。
5. [卓易通官网](https://www.droitong.com/)是应用来源入口，但此项不证明已获得 Pro Max 系统内的容器服务、镜像和驱动依赖。

此次检索尚未定位到**能核验机型、区域与版本的 Pro Max 国行 HarmonyOS 7 全量包公开直链**，因此没有下载其他机型包来冒充供体。当前没有可供审计的目标供体，Pro Max 迁移尚不能开始实际打包。

## 可以推进的取得方式

由拥有匹配国行原机的人，使用官方软件更新取得目标版本，再分享合法取得的更新包或实际下载地址及版本信息。优先取得完整基础包和配套 cust/preload 包；如果得到的是差分 OTA，需要对应旧版本全量输入，不能直接当作完整 system 镜像。也可以使用有明确原始上传者、型号、版本与校验信息的公开分享，先核验内容再采用。无需分享华为账号、设备账号令牌或个人数据备份。

作者公开的 [OTA 获取与解包记录](https://wrlus.com/harmonyos-next-security/extract-huawei-ota-package/)描述了其设备更新请求中取得下载地址的方法。这是历史实测线索，不保证本型号和当前版本仍使用相同协议，也不能从示例 URL 推算 Pro Max 的包地址。若需要网络记录，只能由设备和网络所有者在授权环境操作。

对方提供信息时需包含：设备完整型号、国行/海外区域、起始版本、目标完整版本号、每个文件名及大小、全量/差分标识、来源地址和可用的官方校验信息。下载后自行计算 SHA-256，检查包内产品/版本和签名信息，保留原件只读，解包到单独目录；哈希一致性不能代替来源和签名验证。

## 拿到包后的解包与审计

- [OpenHarmony 官方 update_packaging_tools](https://gitee.com/openharmony/update_packaging_tools)可用于研究格式与工具链。
- [runassu 的 update.bin 解包工具](https://github.com/runassu/HarmonyOS-NEXT-Update-Package-Unpack-Tool)提供结构说明和哈希检查选项。
- [SimomYung 的解包项目](https://github.com/SimomYung/unpack_huawei_package)公开测试包和解析实现；其 README 所列其他设备的包不是本目标供体。

这些只是候选解包工具，尚未在 Pro Max HarmonyOS 7 包上验证。先审查选定版本源码，校验输出分区哈希/长度及包中记录；存在格式差异、签名或加密限制时记录实际错误，不跳过校验声称成功。文件系统提取后运行 [audit_donor.py](../tools/audit_donor.py)，重新评估闭源 HDI/系统库 ABI 和现有补丁，不沿用 MatePad Air 偏移。
