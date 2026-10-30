# 可重复应用的 ELF 补丁：开机动画 EOF

已验证：原 init 以 graphics UID1003 和原生 token 启动原播放器，修正后读取全部300张 PNG。此模块修复资源读取，不代表显示、桌面或整包移植已完成。

`patch.json` 记录完整输入/输出 SHA256、周边指令保护以及三个字节区间。它为原读取循环增加 EOF 提前结束；负值错误、NULL、缓冲区边界、溢出和 CFI 检查保留。现有 RX 段只向前扩到经验证为零的 ELF 填充区域，现有函数地址和重定位不变。

使用 Python 3（Windows/WSL/Linux 均可）：

```text
python apply_guarded_elf_patch.py --manifest patch.json --input bootanimation.original --output bootanimation.patched
```

输入应为当前原包解出的 ELF：SHA `f019c8fbf7a263d5e4f0e6440e206bcb40b622964065b75b9da383535ba5910b`。输出 SHA 应为 `1947fcb520bc5794103c2ef4777a3e0ab225640485d4d7a2c7a8934eb9f3bbd0`。其他版本会拒绝应用，需要重新定位，不能直接套偏移。

工具要求输入输出不同、输出不存在，先校验全部改动和最终 SHA 才创建新文件。不会刷机或修改原文件。后续 vendor 的确认修正可以用同一清单格式封装；每个模块需单独实测。当前没有把无效的回调同步候选或 generic RenderContext 候选加入本模块。
