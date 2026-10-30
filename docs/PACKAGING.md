# 当前源码清单 / Current source inventory

本仓库只保留各功能当前选定的实现及其依赖。旧版源码、失败实验、逐版镜像脚本和重复报告已从当前文件树删除。`SOURCE-SELECTION.json` 记录组件版本、逐文件来源及最终 runtime 对照；旧稿可通过 Git 历史追溯。

This is a current-only source tree. Shared code and required ABI layers are retained. It is not a full ROM or an automatically proven stable system.

维护源码后运行：

```sh
python3 tools/refresh_manifest.py
python3 tools/verify_sources.py
```

- `SOURCE-MANIFEST.json`：文件路径、字节数和 SHA-256，排除自身及 `SHA256SUMS`。
- `SHA256SUMS`：文件与 manifest 的校验值。
- `RELEASE.json`：当前选取策略和功能基线。

上述命令不生成 ZIP、不上传 GitHub，也不触碰设备。编译产物、原厂库、固件、设备备份、账号令牌和私人日志不应提交。个人路径、序列号与网络标识已在发布副本脱敏；构建前配置本地依赖。

See [BUILDING.md](BUILDING.md) for external inputs and [PROVENANCE.md](PROVENANCE.md) for attribution and licensing boundaries.
