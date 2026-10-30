# 尚未真机验收的原生服务候选

此目录未打包、未刷入、未启动。保留原包 UID/原有 GID/权限/secon，并为 RenderService 增加 graphics 组以访问 SM8550 RAM KGSL/DRM 节点；删除 critical、原有 on-restart 联动和未提供的 Android cgroup writepid，设置 condition/disabled/once。不能称原生服务已验证。

`sheng.debug.start.coredeps=true` 才启动 param_watcher SA3901、concurrent_task_service SA1912。`sheng.debug.start.render=true` 才建原图形 RAM 目录并启动 RenderService。测试后须 stop 并核对残留进程；不得依赖关键服务重启整机。

前置条件：原 KGSL 模块和 RAM 字符节点、gzip 解出 Turnip 并 SHA 验证。v39冷启动、shader/同步/像素读回及原生Rosen像素读回已通过；本机原loader忽略VK_ICD_FILENAMES，必须在RAM vendor overlay的原vulkan_driver_v350.json使用Turnip配置。RAM参数persist.rosen.disableddgr.enabled=1使原生模式变量自行选择Vulkan1，已用无全局变量覆盖的rosen_native_mode验收通过。root契约不代替原UID服务验收。

所有 /data 均为现有 RAM tmpfs，实际 userdata 不接入。显示对象和窗口创建后再尝试 snapshot_display；此配置并未启动 foundation/桌面。
