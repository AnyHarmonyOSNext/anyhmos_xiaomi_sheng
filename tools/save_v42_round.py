from pathlib import Path
from datetime import datetime
import json, subprocess
root=Path(__file__).resolve().parent.parent
r=json.loads((root/'analysis/round-20261027-1657.json').read_text(encoding='utf-8'))
r.update(Title='v42原生权限截图成功但纯黑；物理横屏Mi且无扫描帧',
 DeviceState='v42/ShengExports运行，COM21可读。原UID的3901/1912/3503/RenderService/最小4607正常；真实截图API取得2032×3048纯黑JPEG。物理横屏仍Mi（用户确认），KMS所有平面fb=0。无窗口/桌面。',
 Version='已实刷v42，SHA d2c119982e5a30624ab5441bafde24a25632d1b15ac7929adbd0714883b09daf；原init原生恢复NICE40:40/NOFILE32768:32768，非手工helper。',
 QuotaPolicy='本窗口最新实查已用33%，ordinaryUsageAllowed=true，约21:36重置；约2%–3%善后/1%停止，无新定时安排。',
 Screenshot='output/screenshots/v42-native-display-20261027-1702.jpeg，97655字节，SHA a705b6ea044d63ee09d2b76395bf96bf66e508095ba3bcd1a5ed3b28964a169f。解码2032×3048且所有像素0；真实API输出，仅证明捕获接口，不是桌面/物理画面。')
u={
 '电脑连接':('COM21可读；v42冷启动正常，无并发控制器。','17:10'),
 '鸿蒙init和核心服务':('PID1原nice/nofile冷启动生效。原UID3901/1912/3503及RenderService/最小4607已发布。','16:59–17:02'),
 '桌面 / 窗口 / RenderService':('RS1003有逻辑screen0/3048×2032；物理仍横屏Mi。debugfs KMS所有plane fb=0。最小foundation仅4607，无AMS/BMS/WMS/桌面。','17:07'),
 '系统截图':('原init capture-only UIDshell角色经原3503权限服务成功运行snapshot_display；取得2032×3048全黑JPEG，与物理横屏Mi不同。','17:02'),
 '调试终端':('COM21可读；摄像头当前未对准平板，已释放，不再次拍摄房间。','17:10')}
for c in r['Components']:
 if c['Name'] in u:c['State'],c['VerifiedAt']=u[c['Name']]
r['Passed']=['v42冷启动通过，原NICE40和NOFILE32768生效，原UID服务含SA3503正常。','原init给仅CAPTURE_SCREEN的一次性shell角色分配真实token，原截图命令成功；新Receive-ProbeFile逐块校验取回JPEG。','截图解码及全像素统计已执行，确认纯黑/竖向；未把其称为桌面。','KMS所有显示平面fb=0，证明当前没有OS扫描帧提交，符合用户物理横屏Mi观察。','原bootanimation20秒限时诊断发现code20480回调被RS原权限检查拒绝；官方源与本包反汇编均确认该请求使用TF_ASYNC。']
r['Unfinished']=['真实桌面/窗口/首帧均未完成；全黑截图不能作为出图验收。逻辑旋转与物理方向不一致仍需定位。','异步Binder的calling PID可能导致code20480拒绝，尚未证实；AnyHarmonyOS参考补丁input hash与本包不同，不能直接套偏移。','原开机动画无回调/无连接屏，尚未走到绘图；可能还缺图片资源。','KGSL加载有既知device_links_driver_bound WARN，非致命但未修复；Zink未部署，WiFi未开始。']
r['Next']=['按本包PT_LOAD/符号/完整SHA/周边指令guard生成仅客户端TF_ASYNC→TF_SYNC的候选，原服务器检查保持。','仅RAM overlay新inode替换DSO，核对补丁前后完整SHA，再限时运行原bootanimation观察回调及首帧。','继续真实RS→GPU→HDI→KMS链路，不将逻辑尺寸或黑图当作显示成功；有完整帧后再处理方向/桌面。']
r['Evidence']+=['output/v42-manifest.json','analysis/v42-native-screenshot-verification.json','output/screenshots/v42-native-display-20261027-1702.jpeg','output/logs/command-shell-20261027-170202-b304d0eeb4e5.log','output/logs/command-shell-20261027-170749-3d97f5fc72c5.log','output/logs/command-shell-20261027-170902-e2debbd1a05a.log','output/logs/command-shell-20261027-170935-678d0a677638.log','output/logs/command-shell-20261027-171019-9a810c26337e.log']
out=root/'analysis/round-20261027-1715.json'
out.write_text(json.dumps(r,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
subprocess.run(['pwsh','-NoProfile','-File',str(root/'output/Save-RoundSummary.ps1'),'-RecordPath',str(out)],check=True)
banner='**'+datetime.now().strftime('%H:%M')+'最新：'+r['DeviceState']+' 当前v42；实际原生截图已取回但纯黑，不能称桌面。回调code20480拒绝，正核对仅客户端同步传输候选，未验证。详见round-20261027-1715.json。**'
p=root/'analysis/续接检查点.md';p.write_text(banner+'\n\n'+p.read_text(encoding='utf-8'),encoding='utf-8')
with (root/'analysis/20261027续接进展.md').open('a',encoding='utf-8') as f:f.write('\n\n## '+datetime.now().strftime('%H:%M')+' v42原生截图与无扫描帧\n\n'+banner+'\n')
