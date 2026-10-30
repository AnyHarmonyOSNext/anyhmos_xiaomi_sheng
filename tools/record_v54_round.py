"""Record verified v54 results and the read-only userdata audit; no device writes."""
from pathlib import Path
from datetime import datetime
import hashlib
import json
import tarfile

r = Path(__file__).resolve().parent.parent
archive = r / 'output/logs/v54-runtime-20261028.tar.gz'
sha = hashlib.sha256(archive.read_bytes()).hexdigest()
assert sha == 'f496e6b7f6834cb7a38d3c7b5244db127cd5963926cfaab3defa28d6144aa6fa'
with tarfile.open(archive) as f:
    assert len(f.getmembers()) == 7
    for member in f.getmembers():
        assert member.isfile()
        assert len(f.extractfile(member).read()) == member.size
t = datetime.now().astimezone().isoformat(timespec='seconds')
body = f'''## {t} v54 实测收尾及真实 userdata 核对（优先于旧记录）

设备 YOUR_DEVICE_SERIAL 已从 v54 正常返回 TWRP，ADB recovery/root 已确认；本次回 Recovery 未触发三启动分区回刷。此前运行 ShengExports 5.15.178 boot、303 vendor_boot、v54 init_boot，后者 SHA256 64eb0c4a66cc122a3e7df8e512829b6f7d58dda048b78f01bdcee6da7e932b1d。没有真实桌面或系统截图，未验收 SceneBoard，不能把旧诊断图案当桌面。

v54 已实刷，原 storage_manager/storage_daemon 纳入。原账户实际生成用户100的 account_info.json，BMS 注册成功，distributeddata 被 samgr 按需拉起，settingsdata 曾实际孵化 PID878，随后未存活；account.ready 最后仍 false。原账户软件 HMAC 继续使用真实摘要，原 HUKS/TEE未恢复。

本轮运行时补齐 service/chipset/app/misc × el1..el5 父目录，且更新独立 /compat 中 storage-ram-launcher 和 libsheng_ram_no_tee.so；仅可选 IHuksGetInstance(hdi_service,true) 返回不可用，其余转交原实现，不伪造密钥激活成功。新 storage_daemon1073/账户1075由原init启动，旧412/416已结束；桥已在1073映射中验证。但没有走完可选升级路径，不能称其等待已修复。原镜像v54不含上述运行时修改，后续须新版本打包，不能用已改源码重建冒充原v54。

阻点：存储服务曾极高内核CPU，线程栈在私有 sheng_hmos_ipc 的 binder_thread_read，SetBundleQuota 无quota跳过仍耗22–75秒；账户等待存储 PrepareAddUser，未就绪。尚未证明根因是Binder驱动。00:23查询/proc/mounts曾延迟约28秒，之后正常返回；存储1073当次已为S，累计内核CPU仍高。不要把高CPU描述为整轮持续不变，亦不能据此宣称异常解决。

数据实况：Probe 挂载 /dev/loop7 到 /hmos-root/data，ext4；上层 /hmos-ram 是2GiB tmpfs，真实 userdata 没接入鸿蒙，重启不保留此RAM数据。回TWRP后只读核对发现 /dev/block/sda29 已挂载 /data，F2FS，793GiB总量、约788GiB可用；顶层 ls -la 只看到 recovery，未发现 /data/media/0、user_de、system_de、misc/vold/user_keys。ro.crypto.state/type为空，不能据此宣布加密状态或全部数据为空。此前“旧加密数据阻止接入”没有现场依据；主要原因是沿用早期隔离设计，还没实施持久化接入。没有格式化、改写userdata文件或运行原分区初始化。

下一步应先验证真实分区在Probe内的挂载及隔离持久化方案，保留 recovery 目录和现存内容；独立数据镜像/目录优先评估，不能把挂载成功等同鸿蒙账户/加密兼容已完成。用户本次问原因，没有授权清空分区。原服务异常需结合冷启动复核，不能承诺接入userdata就进桌面。新版本先固化父目录和RAM桥，防止热重启状态污染；账户ready→SceneBoard→原GPU/RS真实显示→系统截图。

7份RAM日志已打包取回 output/logs/v54-runtime-20261028.tar.gz，267905字节，SHA256 {sha}，串口传输哈希及本地tar/gzip全量读取均通过。原始证据包括 command-shell-20261028-000227-2f7817636157.log、001327-e038f9688f7b.log、001424-23c07e3b1f21.log、001825-f1565db1faa3.log、001920-e3ccabf7a395.log、002448-094955d05cf8.log，以及 v54-recovery-userdata-audit-20261028.txt、v54-recovery-data-directories-20261028.txt、v54-recovery-data-layout-20261028.txt。后者均在 output/logs。第一次审计误用 /bin/busybox 未成功，后改 /busybox；tar -z因无gzip命令链接失败，改显式 /busybox gzip 后成功，不将失败包当有效备份。

停止时Recovery ADB可读，没有继续启动新实验；无并发串口、无摄像头、无commit/push、无新增定时任务。所有修复仍独立 /compat，不修改/覆盖vendor；数值额度查询工具仍不可用，不能声称已查实际百分比。
'''
for name in ['analysis/续接检查点.md', 'analysis/轮次总结.md', 'analysis/20261027续接进展.md']:
    p = r / name
    p.write_text(body + '\n' + p.read_text(encoding='utf-8'), encoding='utf-8')
(r / '当前状态.md').write_text('# 当前移植状态\n\n' + body, encoding='utf-8')
p = r / 'analysis/v54-framework.json'
obj = json.loads(p.read_text(encoding='utf-8'))
obj.update(status='FLASHED_ACCOUNT100_CREATED_STORAGE_NOT_READY_RECOVERY_CONFIRMED',
           desktop=False, account_ready=False, account100_file_created=True,
           runtime_changes_in_image=False, recovery_adb_confirmed=True,
           userdata_in_harmony=False, recovery_userdata_fs='f2fs',
           ram_log_archive=str(archive.relative_to(r)), ram_log_sha256=sha)
p.write_text(json.dumps(obj, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
print(t)
print('Verified archive and updated current status, three journals, and v54 manifest.')
