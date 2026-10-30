# sheng 原包屏幕回调同步传输候选

状态：仅离线生成和反汇编核对，设备测试未执行。17:51的COM请求没有任何回包，不能把命令已发送当作补丁已应用。

本包 `librender_service_base.z.so` 的 `SetScreenChangeCallback` 在VA `0x89d798` 将 `MessageOption::SetFlags` 参数设为1（异步），随后发送code20480。原RenderService明确拒绝这一请求，原bootanimation等待10秒没有屏幕回调。

候选仅把该客户端参数改为0（同步）。Linux Binder异步请求没有同步调用栈所提供的sender_pid；是否是本次拒绝的实际原因，需要设备前后日志确认。服务器权限、token及调用方检查不变。参考AnyHarmonyOS的同类方案，但其SHA/偏移与本包不同，未直接套用。

`manifest.json` 保存本包完整输入/输出SHA、PT_LOAD换算的文件偏移和周边指令guard；生成器为 `tools/prepare_render_callback_sync.py`。`apply-ram.sh` 还要求既有Probe RAM overlay和tmpfs，复制为新inode、修改4字节、验证完整输出SHA后原子替换。重启即恢复原只读下层。不要对原system镜像或物理分区执行。

下步：COM恢复后检查实际设备状态；应用RAM候选，限时运行原bootanimation并比较code20480/回调/连接屏/首帧日志。该程序是原生绘图链路诊断，不是桌面。KMS仍须看到真实非零fb，物理画面与系统截图均须另验收。
