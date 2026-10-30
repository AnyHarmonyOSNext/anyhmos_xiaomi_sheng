from pathlib import Path
from datetime import datetime
import tarfile, hashlib
r=Path(__file__).resolve().parent.parent
p=r/'output/logs/v56-persistent-20261028-012831.tar'
with tarfile.open(p) as t:
    for m in t.getmembers():
        assert m.isfile() and len(t.extractfile(m).read())==m.size
body=f'''## {datetime.now().astimezone().isoformat(timespec='seconds')} v56 实测与 v57 冷启动进行中

v56实刷验证：ShengExports5.15.178 boot、303 vendor_boot、init_boot SHA331ef2499bcbb66c3c41da2d00c45969faa1477655861a4e568a82235079f6be。原storage先启动，sdc filecrypt init_main_user ret0。settingsdata曾实际存活PID789，账户ready约两分钟完成；SceneBoard反复孵化至屏幕会话初始化、initIconResourceCache。原主题/壁纸、完整窗口4606/3704已纳入。独立EL5桥仅对installs返回-ENOTSUP，已在maps核对，没有伪造加密成功。

v56未获得真实桌面或新系统截图；旧v55系统图仍全黑。01:27现场发现已再次重启到Probe HOLD，boot_id e40ed645-2660-4306-87c1-2f57abcfefca，uptime169秒；鸿蒙根/进程均不在。原因尚未确定。随后正常返回TWRP/ADB/root，无需三启动分区回退。

已导出全部4份v56原始日志：{p.relative_to(r).as_posix()}，{p.stat().st_size}字节，SHA256 {hashlib.sha256(p.read_bytes()).hexdigest()}。本地逐成员读取验证通过，分析副本analysis/v56-logs。v56-live最后6.7MiB，SceneBoard多次THREAD_BLOCK_3S，原JS存在任务池ReferenceError，不能未经调用栈确认就归为主进程致命错误。

非正常重启使8GiB独立数据镜像需ext4 journal replay；自动loop只读挂载不能重放，ro,noload读取出现deleted inode referenced。先在Recovery完整复制普通镜像到/data/hmos-compat/data-v1-v56-before-journal.ext4（保留原大小/权限），再以可写loop承载只读ext4挂载，原journal自动恢复后4份日志完整可读。未fsck或格式化真实分区。数据镜像保留、真实userdata原有内容保留。

调试器发现原PTRACE_EVENT_FORK对不exec的JS应用长期逐syscall跟踪，可能放大冻结。v57改新fork应用立即event/signal模式、早停用PTRACE_CONT、非syscall轮询5ms。PID1早期必要跟踪保留。v57已完整解包验证并01:29实刷，Probe SHAab1f4175e6c0837d1c5f01ad555b5d587721a9a9942537e0cf0743ebbeddb7ca；尚待ipc→hmos及桌面链冷启动，不能声称问题已修复。

兼容修复仅/compat，vendor/vendor_dlkm不改不覆盖；无commit/push、无委派、无新定时任务，摄像头关闭。真实userdata仅独立普通数据镜像后端接入已获用户后续要求支持，早期“不接入”隔离限制被此后续接入要求取代；禁止清空原分区仍有效。额度数值工具不可用。
'''
for name in ['analysis/续接检查点.md','analysis/轮次总结.md','analysis/20261027续接进展.md']:
    f=r/name;f.write_text(body+'\n'+f.read_text(encoding='utf-8'),encoding='utf-8')
(r/'当前状态.md').write_text('# 当前移植状态\n\n'+body,encoding='utf-8')
print(body.splitlines()[0])
