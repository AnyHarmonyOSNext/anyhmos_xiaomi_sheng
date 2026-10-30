# Turnip / OHOS native buffer 与 Zink

上游 Mesa 固定提交 `ea74a6339917390657db153cb9792f9ccac9f5ae`。原底包使用旧 OHOS external-memory 结构编号 1000452001–1000452005 与 native-buffer 编号 1000453001–1000453003。

native-buffer 补丁提供 DMA-BUF 导入、显式同步与 Rosen/Skia NV12 externalFormat 24；未知格式必须拒绝。`tu_ohos.cc/h` 是补丁引用的新文件，需放入 Mesa `src/freedreno/vulkan/`。

本次保留 v99 修复：Zink 不再强制 GLES/GL 版本；Turnip 导入原生交换链图像时不提前计算布局，由 BindImageMemory2 路径计算一次。原工作区独立 GPU 回归通过，壁纸仍黑，后续壁纸实验暂停。

交叉编译 ini 是路径示例。具体参数、步骤与产物见 [BUILD](../../../docs/BUILD.md)。`build_contract.py` 生成 RGB/NV12 与 guard 契约，`build_swapchain_contracts.py` 生成交换链和 EGL 回归程序；均不自动操作设备。
