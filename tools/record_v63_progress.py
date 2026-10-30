from pathlib import Path
from datetime import datetime
import hashlib
import tarfile

r = Path(__file__).resolve().parent.parent
archive = r / 'output/logs/v63-persistent-20261028-022225.tar'
with tarfile.open(archive) as t:
    for m in t.getmembers():
        assert m.isfile() and len(t.extractfile(m).read()) == m.size
body = f'''## {datetime.now().astimezone().isoformat(timespec='seconds')} v63 已测收档，v64 构建验证通过

v62实测失败：appspawn早期LD_PRELOAD整份WiFi SDK后未存活，没有SceneBoard；日志有多次SIGSEGV，尚未完成每个fatal的归属核对，不武断归为构造器。已撤回此预加载，正常回TWRP收档。v62原日志output/logs/v62-persistent-20261028-015811.tar，3755008字节，SHA f38891e9ee1b39eb07e03784ab1a182fb1e0cb4ce0dfd2dd306345ed44bbae55。

v63实刷SHA ebd3ad907d23d5309bfb399db66cf90dde7bdc3dd8ad6a27def035367e75523c，boot_id9e91b23e-eed6-404c-bce7-e3bceca10a43。ipc实际result0后hmos，sdc ret0，账户ready=true，appspawn469正常、原SceneBoard890/1396实际运行。SDK仅从/compat bind到system RAM视图，现场两路径SHA均e5acdc59bdf38e17d19110863acd015373a081835f6c3c5ab8c7e94643e4a13f。原WiFi查询GetWifiDetailState实际38微秒、0ms返回失败1，未伪造联网成功；日志未再见SceneBoard的THREAD_BLOCK。应用已继续Dock/图标/窗口布局、RS CreateNodeAndSurface和DrawHardwareEnabledNodes，但不能以此宣称物理桌面完成。

真实新阻点：SceneBoard两次以JS_ERROR退出，Error code500001，Internal error. get font-scale failed；完整栈在ClockTimeHdsMaterialHelper.getFontSizeHds→锁屏MainPageVc.doInit，原UiAppearance客户端GetSystemAbility失败。原ui_service.cfg/profile证明SA7002是字体缩放/外观服务，现配置未启动。不是继续猜WiFi/GPU导致该JS退出。v64增加原ui_service及原uid/gid/权限、显式sheng.debug.start.ui门控，/compat配置携带；不改vendor。v64已构建/完整解包验证，Probe SHA339bfc1411e5f331a537304d02b471425fb2413d62af37319e47538dd0f5a13c，尚未实刷。下一轮先启动ui gate并核对Publish7002，再验证锁屏/桌面持续运行及新截图。

v63新截图output/screenshots/v63-display0.jpeg，2032×3048、97655字节，PIL各RGB通道extrema均(0,0)，确认全黑，仍无桌面验收。v63 uptime333秒主动正常返回TWRP/ADB，无三启动分区回退；本轮没有观察到自动重启，不能称既往重启问题修好。

完整日志output/logs/v63-persistent-20261028-022225.tar，{archive.stat().st_size}字节，SHA {hashlib.sha256(archive.read_bytes()).hexdigest()}，逐成员读取验证通过，analysis/v63-logs。collector output/logs/persistent-probe-9e91b23e-eed6-404c-bce7-e3bceca10a43.log，1570710字节，SHA d54d6eb0586674ef1705806bb27fc7952b6e3bcb70b30fd7badaf481aa36efda。

原镜像和真实userdata原内容保留；所有兼容修复独立/compat，system仅RAM挂载，vendor/vendor_dlkm不改不覆盖。无commit/push、无委派、无新定时任务，摄像头未开。无额度数值工具，不能声称查过百分比。目标未完成，继续推进。
'''
for n in ['analysis/续接检查点.md', 'analysis/轮次总结.md', 'analysis/20261027续接进展.md']:
    p = r / n
    p.write_text(body + '\n' + p.read_text(encoding='utf-8'), encoding='utf-8')
(r / '当前状态.md').write_text('# 当前移植状态\n\n' + body, encoding='utf-8')
print(body.splitlines()[0])
