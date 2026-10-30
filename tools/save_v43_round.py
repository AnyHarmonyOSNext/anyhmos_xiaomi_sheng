from pathlib import Path
from datetime import datetime
import json,subprocess
r0=Path(__file__).resolve().parent.parent
r=json.loads((r0/'analysis/round-20261027-1715.json').read_text(encoding='utf-8'))
r.update(Title='v43原身份回调与300帧解码通过，Vulkan原生缓冲绑定失败',
 DeviceState='v43/ShengExports运行，COM21可读。原UID服务及最小4607保留；原init graphics1003身份的bootanimation回调/绘图节点成功。EOF修正后300帧资源读入成功，Vulkan SetSkContext适配生效，但原NativeBufferUtils的vkBindImageMemory2失败，无物理首帧或桌面。原生动画已停止，无后台动画/摄像头。',
 Version='实刷v43，SHA038d41dcbca899bbd89b69a039819c566102f097d0aeda8a7cf0ba0c9bf1b7db；原NICE40/NOFILE32768。bootanimation/配置/小型上下文适配仅RAM工作副本。',
 QuotaPolicy='18:02本窗口已用41%，允许执行；约2%–3%善后/1%停止规则不变，无新定时任务。',
 Storage=r['Storage']+' 用户新增授权：可修改底包工作副本和vendor，已验证修正整理成可重复应用补丁；不要求底包工作副本永远不变。')
u={'电脑连接':('用户重启后COM21恢复；目前可读。上轮长驻失联原因未定。','17:54–18:18'),
 '鸿蒙init和核心服务':('v43冷启动原限制生效、原身份服务正常。新增原bootanimation UID1003/token由init分配，原服务器检查保留。','18:02'),
 '桌面 / 窗口 / RenderService':('原bootanimation收到screen0并创建3048×2032节点；300帧资源读入，GPU上下文已设入原Surface。vkBindImageMemory2失败，KMS plane仍fb0。最小foundation只有4607，尚无桌面。','18:16'),
 '系统截图':('v42原native角色取得纯黑2032×3048 JPEG；v43抓帧仍黑，RAM JPEG尚未再次传回。无桌面截图。','17:02及18:16'),
 '调试终端':('COM21可读，无并发控制；摄像头关闭。原生bootanimation已通过stop gate停止。','18:18')}
for c in r['Components']:
 if c['Name'] in u:c['State'],c['VerifiedAt']=u[c['Name']]
r['Passed']=['用户重启后调试连接恢复；v43冷启动，原bootanimation身份graphics1003及真实token成功接收屏幕回调，证明无须参考render-caller-pid补丁。该候选未打包、当前RS库为原版。',
 '源/原包反汇编确认ReadImageFile在EOF时仍memcpy_s，精确SHA/指令guard的EOF修正保留负值/NULL/边界/溢出路径，通过原播放器读取300帧。',
 '只放开通用RenderContext初始化的context-v2候选没修好Vulkan，已从实际real播放器移除；不能计作通过修正。',
 '小型LD_PRELOAD适配原public SetSkContext：使用原RsVulkanContext/GetDrawingContext、实际Surface对象；原vtable与完整DSO SHA先核对，真实UID1003/token继承，未改全局GPU模式或权限。日志确认已设置上下文，推进到vkBindImageMemory2失败。',
 '全尺寸3048×2032/stride12288的真实DMA+原SurfaceBuffer fixture，原尺寸24969216与padding25165824均成功Vulkan绑定。因此“仅分配尺寸不足”假设未获支持，不盲改allocatorpadding。']
r['Unfinished']=['真实RS→GPU→HDI→KMS首帧与桌面未完成；所有plane fb0，物理仍以用户最近横屏Mi观察为准。',
 '当前真实阻点：原NativeBufferUtils报vkBindImageMemory2失败，需取得真实图像格式/extent/layout与native handle差异；不能用fixture成功等同原客户端通过。',
 '逻辑截图仍竖向纯黑；需首帧后继续方向和窗口/桌面。GPU模块WARN、Zink、WiFi状态同前。',
 'metadata导出180008包含既有日志；重启后的Probe曾报persistent unavailable，不能宣称新一轮全部日志已持久写入metadata。本轮COM日志保存在电脑。']
r['Next']=['针对失败点补充Turnip OHOS绑定错误诊断；保持既有验证通过版本及回退，按真实错误决定Mesa/vendor修正。',
 '把确认有效的EOF和原init身份配置整理成可重复应用补丁；上下文适配标记部分通过，未声明已修好显示。',
 '首帧实际提交后核对物理面板与系统截图；后续窗口/桌面仍需AMS/BMS/WMS等。']
r['Evidence']+=['analysis/v43-image-verification.json','output/v43-manifest.json','output/logs/20261027-180008','output/logs/command-shell-20261027-175652-c253c628812b.log（参考回调候选仅root测试失败）','output/logs/command-shell-20261027-180158-25acc51723c0.log（原身份回调/节点成功）','output/logs/command-shell-20261027-180348-ed3e4532df71.log（原EOF失败）','analysis/bootanimation-eof-patch.json','output/logs/command-shell-20261027-180808-8cc64f3a0f5f.log（300帧成功，ctx缺失）','analysis/bootanimation-context-patch.json（单纯generic初始化未修好，已移除）','analysis/bootanimation-vulkan-adapter-build.json','output/logs/command-shell-20261027-181607-1edf307d7f89.log','output/logs/command-shell-20261027-181632-37ae18bd4882.log（allocator成功，vkBindImageMemory2失败）','output/logs/command-shell-20261027-181833-35afc748a377.log（全尺寸两种size均绑定成功）']
out=r0/'analysis/round-20261027-1820.json';out.write_text(json.dumps(r,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
subprocess.run(['pwsh','-NoProfile','-File',str(r0/'output/Save-RoundSummary.ps1'),'-RecordPath',str(out)],check=True)
banner='**'+datetime.now().strftime('%H:%M')+'最新：'+r['DeviceState']+' 全尺寸原大小与padding fixture均绑定成功，不盲改padding。用户已允许修改底包工作副本/vendor，保留原包/备份。详见round-20261027-1820.json。**'
p=r0/'analysis/续接检查点.md';p.write_text(banner+'\n\n'+p.read_text(encoding='utf-8'),encoding='utf-8')
with (r0/'analysis/20261027续接进展.md').open('a',encoding='utf-8') as f:f.write('\n\n## '+datetime.now().strftime('%H:%M')+' 原客户端进入Vulkan绑定\n\n'+banner+'\n')
