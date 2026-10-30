from pathlib import Path
from datetime import datetime
import json,subprocess
r0=Path(__file__).resolve().parent.parent
r=json.loads((r0/'analysis/round-20261027-1820.json').read_text(encoding='utf-8'))
r.update(Title='原bootanimation→GPU→RenderService→HDI→双平面真实诊断出图验收通过',
 DeviceState='当前v43/ShengExports/COM21可读。原init graphics1003/token的原bootanimation已真实GPU绘制并经RenderService/HDI提交，KMS plane0与plane6均fb283；用户明确确认看到了黄边/左青右粉诊断图。动画已停止。尚无鸿蒙桌面，截图API的最近电脑已核验结果仍为v42纯黑。',
 Version='实刷v43 SHA038d41dcbca899bbd89b69a039819c566102f097d0aeda8a7cf0ba0c9bf1b7db；RAM已修EOF/SetSkContext/OHOS标志，RS4137和foundation4165重启加载。候选v44 SHA cb8049a21616b0db7ab203c3e8ab30ef6521ff389ccdd6dc1a1cec41389bf228 已构建解包，尚未刷。',
 QuotaPolicy='18:32本窗口实查已用71%，ordinaryUsageAllowed=true；约2%–3%善后/1%停止规则不变，无新定时安排。')
u={'实际扫描与色条':('新增真实原bootanimation经原GPU/RS/HDI全链提交；plane0+plane6 fb283，用户确认黄边左青右粉诊断画面。此前手工扫描验收保留。','18:30–18:32'),
 'GPU':('原shader及Rosen已通过；现在原bootanimation真实SurfaceBuffer/allocator IPC/Vulkan导入→绘图→RS/HDI→物理平面也通过，非handle fixture结论替代。','18:30–18:32'),
 '桌面 / 窗口 / RenderService':('原native RS绘图诊断实际出图通过，原token/权限/CFI保留。最小foundation仍仅4607，AMS/BMS/WMS/桌面未启；不要称进桌面。','18:32'),
 '系统截图':('v42电脑核验JPEG仍纯黑；v43新JPEG大小97655但未取回做全像素统计。实物出图已由用户确认，API捕获内容仍需定位。','18:30'),
 '电脑连接':('COM21可读，当前无并发控制；准备回Recovery收日志后v44冷启动复验。','18:35')}
for c in r['Components']:
 if c['Name'] in u:c['State'],c['VerifiedAt']=u[c['Name']]
r['Passed']+=['诊断驱动精确证明：原客户端绑定格式37/原格式12、extent3048×2032、stride12288、size24969216均一致，但重复布局算成50036736。原CreateVkImage使用0x8000原生标志，当前Mesa头定义OHOS=0x2000，导致创建时没有推迟布局。',
 '精确SHA/指令guard补丁只把NativeBufferUtils::CreateVkImage标志改0x8000→0x2000，输出DSO SHA d423413ec1fc58f40c5b04846b00530a4d82d0929eee769ede3bf5c605e5a77d。重启原UID RS及最小foundation后，真实客户端绑定总大小恢复24969216，三次实际buffer导入成功。',
 '真实KMS plane0与plane6均fb283，原composer日志有SetDisplayClientBuffer/SetLayerBuffer/submit；用户回答“看到了诊断画面”，物理出图验收通过。',
 '通用守卫ELF补丁工具/独立EOF模块包已生成，宿主运行输出SHA与设备验收的EOF修正一致。已通过的标志模块也保留独立patch.json，便于合并。',
 'v44把EOF/小型Vulkan适配/标志修正及图片诊断资源随包，原始Turnip v1保留；bootanimation加入已有dev_dma_heap辅助组。8MiB/LZ4/原Android init保留/所有资产解包验证通过，尚需冷启动。']
r['Unfinished']=['鸿蒙桌面/窗口/应用框架尚未启动。已通过的是原生绘图链与诊断画面。',
 'v44仅构建解包，未完成冷启动和新资源全链验收；当前效果依赖v43运行中的RAM修正。',
 '截图接口已能返回文件，尚需取得含真实图案的API截图；物理照片/诊断素材不能替代系统截图。',
 '原composer可选GetDisplayClientTargetProperty指针空、颜色空间metadata设置失败仍有日志，当前诊断已出图，但功能完整性需后续vendor适配；不要把错误全忽略成正常。',
 'GPU module WARN、Zink未验证、WiFi未开始；真实userdata仍未接入。']
r['Next']=['先回TWRP导出当前日志，再刷v44/ShengExports，冷启动后显式ipc/hmos、GPU stage-only、coredeps/render/screen/bootanim门控。',
 '确认随包自动SHA守卫标志修正成功，不再手工上传库；重复原诊断出图并抓KMS/真实API截图。',
 '冷启动链稳固后推进窗口/桌面所需原服务，按实际日志修改vendor工作副本；各轮更新完整状态。']
r['Evidence']+=['output/logs/command-shell-20261027-182644-f0a635e651bc.log（双倍布局诊断）','output/logs/command-shell-20261027-182713-8a195ad3d616.log（Rosen参数fixture通过）','analysis/rosen-ohos-handle-flag-patch.json','output/logs/command-shell-20261027-182912-b1d864aae126.log','output/logs/command-shell-20261027-182952-af9c564dc064.log（plane0/6 fb283）','output/logs/command-shell-20261027-183048-dc692f8db048.log（RS/HDI提交）','用户18:32左右回答：看到了诊断画面','output/sheng-next-elf-patch-v1.zip','analysis/v44-native-inputs.json','analysis/v44-image-verification.json','output/v44-manifest.json']
out=r0/'analysis/round-20261027-1836.json';out.write_text(json.dumps(r,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
subprocess.run(['pwsh','-NoProfile','-File',str(r0/'output/Save-RoundSummary.ps1'),'-RecordPath',str(out)],check=True)
banner='**'+datetime.now().strftime('%H:%M')+'最新：'+r['DeviceState']+' v44仅候选、准备Recovery导出再冷测。见round-20261027-1836.json。**'
p=r0/'analysis/续接检查点.md';p.write_text(banner+'\n\n'+p.read_text(encoding='utf-8'),encoding='utf-8')
with (r0/'analysis/20261027续接进展.md').open('a',encoding='utf-8') as f:f.write('\n\n## '+datetime.now().strftime('%H:%M')+' 原GPU/RS全链物理验收\n\n'+banner+'\n')
