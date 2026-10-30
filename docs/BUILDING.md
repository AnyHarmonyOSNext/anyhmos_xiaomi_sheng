# 构建边界 / Build boundaries

本包是研发源码快照，不是完整 ROM 或一键构建环境。This is a development source snapshot, not a full ROM or turnkey build environment.

## 外部输入 / External inputs

| 输入 / Input | 用途与限制 / Purpose and limits |
| --- | --- |
| 小米 sheng 官方 OS3.0.303.0.WNXCNXM Android 16 基线 | 匹配的分区、模块、配置与固件。Original matching partitions, modules, configuration and firmware; obtain independently. |
| 项目使用的 MatePad Air HarmonyOS NEXT donor | 原系统用户态、原 HDI/框架与链接输入。Proprietary userspace and link-time inputs; not redistributed. The marketing name alone is insufficient to reproduce a build: check each recipe's input hashes. |
| 匹配的 boot/init_boot/vendor_boot 基线 | 大多数镜像脚本按前一版镜像增量构建并严格检查 SHA-256。Most image builders require a specific earlier image; a v145 script does not build v143 from nothing. |
| HarmonyOS native SDK | 当前开发布局为 SDK `6.0.0.47`；需要 AArch64 OHOS Clang、链接器、头文件等。SDK binaries are not bundled. |
| Android common 内核与工具链 | Commit `6f2f96be86b93de6ed58a2c46b456fb49734c382`，匹配 303 配置；历史 IPC 构建记录使用 Android clang r450784e / 14.0.7。Review symbol-version and CFI requirements before reproducing a kernel/module build. |
| 公共上游源码 | 精确版本见 `external/upstream-sources.json`。Unmodified upstream repositories are represented by commit pins; local changes and added files are exported separately. |
| 运行环境 | 主机脚本为 Windows PowerShell，原生/内核构建主要在 WSL Linux；Python 3、Git、C/C++ 构建依赖按对应脚本准备。 |
| 其他工具 | `magiskboot`、ADB/fastboot、libdrm/Mesa 等按脚本准备。Proprietary extracts and executable tools are excluded from the source package. |

## 开发布局 / Development layout

主要 WSL 路径为 `/root/hmos-work` 和 `/root/hmos-reference`。部分历史脚本的 Windows/WSL 工作区路径已在发布副本中替换为 `C:/SHENG_WORKSPACE` 或 `/mnt/c/SHENG_WORKSPACE`，设备序列号变为 `YOUR_DEVICE_SERIAL`。这些是占位值，运行前必须配置。

The historical WSL layout uses `/root/hmos-work` and `/root/hmos-reference`. Publication removes private host paths and serial numbers from the copied sources. Configure these assumptions before running a script. The live development workspace is not rewritten by this export.

`external/custom/sheng-graphics-port/` 对应 WSL 的 `graphics-deps/sheng-graphics-port/`；其余 `external/custom/<name>/` 对应工作根目录下同名工程。`external/patches/<name>.patch` 应用于记录的上游 HEAD；`external/overlays/<name>/` 是同一版本下的新增源码。不能把某次实验的整个 Mesa diff 与其他版本补丁盲目叠加。

Restore custom sources to the expected development layout, check out exact upstream commits, then review/apply the selected patches and overlays. The Mesa worktree diff is a development snapshot that includes experimental changes; it is not an accepted universal runtime patch.

## v145 的实际构建链 / Actual v145 build chain

1. 准备上述 SDK、上游头文件、libdrm 静态库和 donor 链接库，并核对对应哈希。Prepare the external SDK, headers, libdrm and donor linking inputs.
2. 在 WSL 审查/运行 `tools/build_screen_power_v145.py`，生成兼容 composer。Review/run this script in WSL to compile the OFF latch fix.
3. 正确顺序唤醒程序来自 `tools/native_display_wake_v2.cpp`。其编译产物需自行重建到脚本要求的位置；源码包不携带无扩展名 ELF。Rebuild the helper required by the image recipe; its binary is deliberately absent.
4. 在具备 `vendor_ramdisk_edit.py` 所需工具的 Windows 环境审查/运行 `tools/build_vendor_screen_power_v145.py`。它以已有、精确匹配的 v143 镜像为输入，仅替换 composer、唤醒 helper 和 manifest，校验其他 ramdisk 条目、DTB、bootconfig 与容器往返。The v143 baseline image must already exist.
5. 产物成功构建并不等于功能通过。v145 已上机且短按熄屏获用户实测确认；深睡和长期待机仍需另验。v145 screen-off has user acceptance; deep sleep and long-term standby still require separate validation.

具体命令参数和输入以脚本为准。不要为“跑通脚本”删除哈希、分区、机型或槽位检查。Use each recipe's actual arguments and preserve its input/product/slot checks.

## 调试 / Debugging

COM 串口运行的是开发 probe 协议，不是 ADB shell。`output/Invoke-ProbeCommand.ps1` 将 UTF-8 shell 命令编码为带请求 ID 的串口消息；`Send-ProbeFileStream.ps1` / `Receive-ProbeArtifact.ps1` 提供文件传输，`Get-NativeScreenshot.ps1` 使用系统截图服务。

The serial probe is a privileged development facility on the unlocked test device. It is not a production security boundary. Use the host wrappers after reviewing their behavior. Commands execute in a different outer root than the Harmony userspace: `/hmos-root` is the chroot root; paths such as input devices may need the `/hmos-root` prefix.

- COM 操作必须串行，前一个进程真正退出后再发下一条。Serialize requests; do not overlap host sessions.
- 每条脚本约 60 秒硬上限；采集窗口应留余量，不要用 90 秒前台采集。Keep captures below the command timeout.
- `CMD END exit=-1 signal=9` 是执行被终止的完整回复，不等于失联；工具已修正负数退出码解析。Distinguish termination from missing replies.
- 系统截图与物理屏幕状态要分开验证。Validate physical panel state independently of captured UI.
- 镜像刷写、userdata 初始化、全局服务 stop/start 和历史 Recovery 工具都需要先审查。No host tool is an invitation to run every historical experiment.

## 分区与恢复 / Partitions and recovery

后续仅更新 `vendor_boot` 的流程要求已经安装匹配开发基线。首次配置仍涉及匹配 boot、最小 init_boot、super 动态分区和 userdata。请依据本机已保存的备份恢复；这个发布包不包含任何设备专属备份。

The current test setup updates `vendor_boot` only after the baseline is established. For a device stuck in fastboot or unable to reach Recovery, the project's established procedure restores its own saved boot/vendor_boot/init_boot trio first. No unknown temporary boot image is supplied here. This is a project recovery convention, not a guarantee for every device or firmware.

源码快照的导出与哈希校验见 [PACKAGING.md](PACKAGING.md)。Source snapshot export and integrity checks are documented separately.
