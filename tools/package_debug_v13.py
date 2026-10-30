from pathlib import Path
import hashlib
import json
import shutil

root = Path(__file__).resolve().parent.parent
out = root/'output'
package = Path('C:/MIO-KITCHEN-PYSIDE6-5.0.0-PREVIEW/hmos/debug-v13')
if package.exists():
    raise SystemExit('Package already exists; preserve it and review before updating.')
readme = '''# sheng 鸿蒙 NEXT 调试包 v13

已在小米平板6S Pro 12.4 真机验证：六个鸿蒙 EROFS 分区可只读挂载，USB COM21 双向日志可用，鸿蒙原生 init 执行了 pre-init、init、post-init。仍是早期移植调试包，尚未进入桌面。

真机内核保持小米303官方 5.15.178；本包修改 init_boot 的启动程序，保留原 Android init 供对照。boot/vendor_boot 使用配套303原版。原 super 和原镜像未修改。

## 当前进展

- 默认开机停在诊断 HOLD，静态 PID1 采集内核日志。原生鸿蒙 init 需要通过串口显式发送 hmos 才执行。
- hmos 使用只读镜像加 RAM overlay，新 /data、/metadata、/log 都在内存；没有向新根暴露实际 userdata 或 metadata 物理分区节点。
- 原全部自动服务配置被遮蔽，只启用 tools/configs/init-core-v13.cfg 中的最小阶段与一次 samgr 测试，无 critical 自动重启服务。
- 真机确认 /dev/access_token_id 缺失，原生权限列表写入 kernel 返回 -2；samgr 启动命令已执行 fork，但随后进程列表未见 samgr，尚未定位该子进程退出点。
- init、samgr 的原生 musl 动态依赖解析均通过。仅此不能证明框架和硬件可用。
- init 日志经 metadata、kmsg 和 HiLog datagram 调试采集器保留。采集器不是完整 hilogd。
- v13 在 HMOS_CORE_START_DONE 后切到事件/致命信号追踪，保留 HiLog/kmsg；此后不逐系统调用拦截 reboot。

## 测试与回退

本包配合已刷入的 hmos super，仅支持 sheng A槽。脚本核对设备、实际备份与镜像 SHA256，写入 boot_a、vendor_boot_a、init_boot_a。不要同时运行多个刷机/串口脚本。

1. 进入已知可用的 TWRP，root ADB 连接。device-backup 中已保留 YOUR_DEVICE_SERIAL 的原机三个启动分区和 Recovery 备份；00-Backup-Recovery.ps1 用于首次备份，已有备份不要覆盖。
2. 进入 fastboot，执行 `powershell -ExecutionPolicy Bypass -File .\\01-Flash-Probe.ps1 -Version v13`。
3. COM21 出现后执行 `powershell -ExecutionPolicy Bypass -File .\\Send-ProbeCommand.ps1 -Port COM21 -Command status -Seconds 3`。端口号需以设备管理器实际枚举为准。
4. 发送 `-Command hmos-list` 仅测新根动态依赖；另一次新启动发送 `-Command hmos` 执行最小鸿蒙 init。hmos-list 退出后 PID1 被暂停，需重启后再测 hmos。
5. `-Command diag` 查看原生进程和 IPC 设备节点；`-Command replay` 重放最多2MiB内存日志。日志会写入电脑 logs。
6. `Return-To-Recovery.ps1` 请求返回 TWRP。若落到 fastboot，按用户要求优先完整回刷原机 boot、vendor_boot、init_boot，再尝试 Recovery；仍失败时手动按已知方法进入 TWRP。
7. 在 TWRP 运行 `02-Collect-Recovery.ps1`，从 /metadata/hmos-debug 导出日志，不格式化 metadata。

`03-Restore-BootChain.ps1` 使用 device-backup 的原机完整备份，仅回退三个启动分区。hmos super 仍保留；恢复这三者不等于恢复完整 HyperOS。Recovery 分区不在刷写脚本范围内。

## 文件与后续工作

- init_boot_hmos_probe_v13.img：默认诊断 HOLD，可用 hmos-list/hmos/diag。
- init_boot_hmos_trace_v13.img：接回原 Android init 的对照实验；已知存在 /debug_ramdisk 根布局不兼容，通常无需重复。
- package-manifest.json、v13-manifest.json：镜像、工具与备份的校验记录。
- 三启动分区回退使用原设备实际备份，尤其 boot_a 的完整192MiB，不能用303包的96MiB文件代替该原机回退备份。

参考源码已克隆到 WSL /root/hmos-reference/AnyHarmonyOS，cb1ce16，保持只读，无提交/推送。它面向 SM8650/6.1，当前只借鉴启动布局及 IPC 适配源码。5.15模块仍在离线适配与 ABI 核对，本包没有包含或加载它们。

工作区 analysis/续接检查点.md 与各轮真实日志记录后续状态。当前桌面、GPU、显示、触摸、加密存储及完整系统服务均未验证。
'''
(out/'使用说明.md').write_text(readme, encoding='utf-8')
names = ['00-Backup-Recovery.ps1','01-Flash-Probe.ps1','02-Collect-Recovery.ps1',
         '03-Restore-BootChain.ps1','Common.ps1','Capture-Serial.ps1',
         'Send-ProbeCommand.ps1','Return-To-Recovery.ps1','使用说明.md',
         'boot_stock_303.img','vendor_boot_stock_303.img','init_boot_stock_303.img',
         'init_boot_hmos_probe_v13.img','init_boot_hmos_trace_v13.img','v13-manifest.json']
verified = json.loads((root/'analysis/v13-image-verification.json').read_text())
for mode in ('probe','trace'):
    binary = out/f'init_boot_hmos_{mode}_v13.img'
    assert hashlib.sha256(binary.read_bytes()).hexdigest() == verified[mode]['sha256']
package.mkdir()
for name in names:
    shutil.copy2(out/name, package/name)
for name in ('platform-tools','device-backup'):
    shutil.copytree(out/name, package/name)
for name in ('hmos_probe_v13.c',):
    dest = package/'source'/name
    dest.parent.mkdir(exist_ok=True)
    shutil.copy2(root/'tools/archive'/name, dest)
shutil.copy2(root/'tools/configs/init-core-v13.cfg',package/'source/init-core-v13.cfg')
def manifest(directory):
    result = {}
    for p in sorted(directory.rglob('*')):
        if p.is_file() and p != directory/'package-manifest.json':
            with p.open('rb') as stream:
                result[str(p.relative_to(directory))] = {'Bytes': p.stat().st_size, 'Sha256': hashlib.file_digest(stream,'sha256').hexdigest()}
    (directory/'package-manifest.json').write_text(json.dumps(result,indent=2,ensure_ascii=False),encoding='utf-8')
    return result
result=manifest(package)
manifest(out)
for name, record in result.items():
    with (package/name).open('rb') as stream:
        assert hashlib.file_digest(stream,'sha256').hexdigest()==record['Sha256']
print(f'Package verified: {package} ({len(result)} files)')
