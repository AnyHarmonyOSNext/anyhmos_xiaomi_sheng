"""Record observed v51 results; do not infer desktop or TEE readiness."""
from pathlib import Path
import json
from datetime import datetime
r=Path(__file__).resolve().parent.parent
stamp=datetime.now().astimezone().isoformat(timespec='seconds')
body=f'''## {stamp} v51 实测与桌面优先路线

v51 已实刷并冷启动，init_boot SHA256 6939760e89a7f29a7930f5da31f0d1a433babe9592fdacec82c9b87e39821bdc。原 native init/HDF/AccessToken 基线工作；本次没有启动 GPU、RS、accountmgr、appspawn、foundation，不能把旧轮次进程写为本次状态。原 HUKS PID407 确实进入华为 TEE，connect errno111，HksServiceInitialize=-65536；已 SIGTERM 结束，串口日志确认 process ended。SA3510 未验收。

完整 hilog 已取回 output/logs/v51-huks-final-20261027.txt.gz，26949字节，SHA256 245c0c8485e4d632f13d3602811915d1908024eee87264f5ada48c22fdd4f01f。设备当前仍运行 v51 Probe，尚未回 Recovery。所有串口操作顺序执行。

用户最新要求先真实桌面和显示，暂停原厂 TEE 研究，允许参考 AnyHarmonyOS 软件 HUKS/成功返回方案。当前参考 commit cb1ce16e71392404ecb56f812380ac18c7085520 的 git grep 和 docs/SECURITY_SCOPE.md 明确软件 HUKS 未纳入，不声称复用了不存在的实现。正在评估仅账户文件摘要所需的软件 HMAC 兼容，给出真实输出，不伪造账户集合，不修改认证密钥。账户启动、BMS401、实际 appspawn、SceneBoard、系统截图仍未完成。方块/色条只是诊断，不重复验收。

vendor/vendor_dlkm 保持只读，兼容修正在 /compat；真实 userdata 未接入。未 commit/push，未开启摄像头，未创建定时任务。工具无可查询数值额度，不能声称实查剩余百分比。停止前仍须回 TWRP、确认 ADB、导出日志并更新状态。
'''
for name in ['analysis/续接检查点.md','analysis/轮次总结.md','analysis/20261027续接进展.md']:
    p=r/name;p.write_text(body+'\n'+p.read_text(encoding='utf-8'),encoding='utf-8')
(r/'当前状态.md').write_text('# 当前移植状态\n\n'+body,encoding='utf-8')
p=r/'analysis/v51-framework.json';a=json.loads(p.read_text());a.update(status='FLASHED_COLD_BOOT_HUKS_TEE_REFUSED_STOPPED',observed_at=stamp,huks_result=-65536,huks_stopped=True,desktop=False,device_state='v51 Probe running; no Recovery yet',full_hilog='output/logs/v51-huks-final-20261027.txt.gz',full_hilog_sha256='245c0c8485e4d632f13d3602811915d1908024eee87264f5ada48c22fdd4f01f');p.write_text(json.dumps(a,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(stamp)
