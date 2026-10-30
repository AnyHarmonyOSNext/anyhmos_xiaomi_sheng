# 源码整理与校验 / Source packaging

`tools/export_release_sources_wsl.py` 与 `tools/package_source_release.py` 可重新生成这一类源码快照。它们不刷机、不连接串口，也不会自动初始化 Git、提交或上传。

The exporters prepare reviewable files without accessing the device or uploading to GitHub. They preserve the development originals and refuse to replace an existing output directory or ZIP.

## 操作顺序 / Workflow

1. 在 WSL 运行导出脚本，指定一个尚不存在的输出目录。它从现有开发环境收集自定义源码、上游提交、差异、新增文件与许可；具体路径见脚本。Run the WSL exporter against the actual development checkouts first.
2. 在 PowerShell 设置 `SHENG_REDACT_DEVICE_SERIAL`，值为本地测试机的真实序列号，仅用于从发布副本移除它。可选的 `SHENG_REDACT_STOCK_IMAGES` 指向本地官方包的 `images` 目录，以替换历史配方中的个人输入路径。不要把实际值写进提交。Set these variables locally; do not commit their values.
3. 从源码根目录运行下例，修改参数为实际路径。Use a fresh destination and archive name for every export.

```powershell
python tools/package_source_release.py `
  --wsl-export work/wsl-source-export `
  --destination release/sheng-source-snapshot `
  --archive output/releases/sheng-source-snapshot.zip `
  --report analysis/source-publication-review.json
```

## 收录范围 / Contents

收录 `tools`、`compat` 的文本源码与配置、文档、WSL 导出，以及 `output` 根目录的 PowerShell 源码。`analysis` 只收选定的补丁、配置、构建与验证报告。历史试验同样保留，不能由此推断它们都应启用。

Images, executable tools, shared libraries, kernel modules, firmware, SDKs, app packages, userdata, private raw logs and screenshots are excluded. Source recipes can still refer to these independently supplied inputs; a referenced filename does not mean the binary is included.

个人 Windows/WSL 工作区路径、测试序列号、文本形式的私网 IPv4/MAC 会替换成占位值；JSON 的 Unicode 转义路径也会处理。发布后的路径和示例网络值需要自行配置。源文件的 SHA-256 以**发布副本实际字节**为准，不是原始开发文件的哈希。

Redaction applies to the copy only. Existing SPDX/copyright notices are retained. This automated pass is a bounded publication check, not proof that every possible sensitive or licensing issue has been identified; review the final file list and provenance before public publication.

## 产物 / Artifacts

- `SOURCE-MANIFEST.json`：每个载荷文件的路径、字节数、SHA-256；排除清单自身和 `SHA256SUMS`，避免递归。
- `SHA256SUMS`：载荷与 `SOURCE-MANIFEST.json` 的 SHA-256。
- ZIP 同目录的 `.zip.sha256`：压缩包本身的哈希。
- `RELEASE.json`：版本、收录范围与发布边界。
- `--report` 文件：本地脱敏计数、扫描结果、ZIP/哈希检查结果，不自动收入公开包。

The packager checks UTF-8/text content, high-confidence credential patterns, redaction rules, README/docs navigation, file hashes, ZIP CRCs, file coverage and extracted bytes. `.gitattributes` preserves bytes across Git checkouts so the manifest can be verified without line-ending conversions.

源码包并不附完整 ROM、所有上游仓库或可直接刷写的镜像。构建要求见 [BUILDING.md](BUILDING.md)，来源和授权边界见 [PROVENANCE.md](PROVENANCE.md)。
