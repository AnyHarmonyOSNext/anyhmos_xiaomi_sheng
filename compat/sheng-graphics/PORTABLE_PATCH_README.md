# sheng 原生显示补丁 v2

已验证设备：小米平板6S Pro 12.4（sheng），当前MatePad Air鸿蒙原包、303底包及ShengExports 5.15.178内核。v43真实出图获用户确认，v44已冷启动复验，两次均经原GPU、RenderService、原HDI和左右扫描平面；已取得3048×2032实际DMA扫描缓冲读回图。尚无桌面，默认snapshot_display API仍返回纯黑。

此包提供可重复的补丁机制和当前版本模块。Python工具对整个输入SHA、指令及最终输出SHA做校验，输出到新文件；不同原包版本需要重新定位。它不会刷机。

```text
python apply_guarded_elf_patch.py --manifest bootanimation-eof/patch.json --input bootanimation.original --output bootanimation.patched
python apply_guarded_elf_patch.py --manifest rosen-handle-flag/patch.json --input librender_service_base.original.so --output librender_service_base.patched.so
```

`bootanimation-eof` 修复原图片读取循环在EOF时的零长度memcpy_s错误，保留负值、NULL、边界及溢出检查。原播放器已读入300张PNG。

`rosen-handle-flag` 只调整NativeBufferUtils::CreateVkImage的OHOS外部缓冲标志：原包0x8000对应当前私有Mesa接口0x2000。原先创建时未推迟布局，绑定时累计成50036736字节；修正后为24969216字节并真实出帧。此模块与当前移植Mesa配套，不应套到原厂华为GPU栈。

`vulkan-context-adapter` 包含小型本地源码和对应产物，补齐原播放器缺失的公开SetSkContext语义，使用原RsVulkanContext/GetDrawingContext和原Surface；对象布局针对本包固定。配套launcher保持原init分配的graphics UID1003和token。运行组包含graphics、data_reserve、dev_dma_heap；原token、调用者、CFI检查保留。

整体启动集成见工作区的tools/create_probe_v44.py、build_probe_v44.py及analysis/v44-native-inputs.json。v44镜像SHA256为cb8049a21616b0db7ab203c3e8ab30ef6521ff389ccdd6dc1a1cec41389bf228。桌面/窗口/输入及WiFi仍需继续移植。后续验证有效的vendor模块可采用同样清单封装；保留原包和三启动分区回退备份。
