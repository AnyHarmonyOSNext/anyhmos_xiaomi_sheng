from pathlib import Path
from datetime import datetime
import json,subprocess
r0=Path(__file__).resolve().parent.parent
r=json.loads((r0/'analysis/round-20261027-1836.json').read_text(encoding='utf-8'))
r.update(Title='v44冷启动真实出图与横屏扫描读回通过，已回TWRP；v45仅离线候选',
 DeviceState='设备YOUR_DEVICE_SERIAL当前TWRP 3.7.1_12-0，ADB recovery/root可读；内核5.15.144。最后已实刷并冷启动验收的是v44/ShengExports，原生GPU→RS→HDI双平面出图，已取回3048×2032实际扫描缓冲PNG。尚无桌面，默认截图API仍为竖向纯黑。原生应用框架15秒限时测试结束，已恢复4607单服务后回Recovery。',
 Version='设备三启动镜像仍为ShengExports boot /303 vendor_boot/v44 init_boot（cb8049a21616b0db7ab203c3e8ab30ef6521ff389ccdd6dc1a1cec41389bf228）。v45候选仅构建解包通过，SHA7136bd72739c4eadbca42b9e785cc3879447034f0d431d90c46e0cc994a3ee3c，未刷入。',
 Kernel='当前Recovery 5.15.144-android13-8-00017-gdaa558ea5602-ab11990578；最后Probe为精确匹配的ShengExports 5.15.178/原CFI/KMI。禁止在Recovery加载5.15.178模块。',
 QuotaPolicy='本窗口最近实查已用89%，允许执行。已提前完成设备善后，不开新真机实验；2%–3%善后/1%前停止规则保留。实际约21:36重置，已询问21:40或明天11:35续接，未收到选择前不新建任务。',
 Screenshot='实际扫描读回：output/screenshots/v44-actual-scanout-20261027-1848.png，3048×2032，SHA86735b3bea2bd838c47924aec1b37e64ce22129c6f3e057a9b2cd9b09db0b241。KMS plane90/fb283、PRIME DMA_BUF同步读出，PNG只编码原始像素；黄边/左青右粉/白方块为原播放器GPU绘制的诊断素材，不是桌面或snapshot_display API截图。API另存v44-cold-api-20261027-1840.jpeg，2032×3048全黑，SHA与v42一致。')
u={'电脑连接':('TWRP Recovery ADB/root已验证，无并发刷写/串口进程，无后台动画或摄像头。','18:52:34'),
 '当前内核':(r['Kernel'],'18:52:34'),
 '鸿蒙init和核心服务':('v44冷启动原NICE40/NOFILE32768、原角色及SHA守卫补丁均通过。额外应用框架6库加载，未证明服务发布；限时后已恢复4607并回Rec。','18:39及18:50'),
 '实际扫描与色条':('原bootanimation实际GPU→RS→原HDI出图：v43用户确认；v44冷启动plane0+plane6 fb66，再次读回plane90/fb283横屏完整图。非早期手工色条结论。','18:39–18:48'),
 'GPU':('真实原SurfaceBuffer/allocator IPC/Vulkan导入/绘图/RS/HDI/KMS链冷启动通过。纠正OHOS handle标志后不再双算布局。长期连续帧与整套桌面尚未验收。','18:39–18:48'),
 '桌面 / 窗口 / RenderService':('原native绘图链真实出图通过；桌面未启动。legacy libwms在SceneBoard原包不提供，不应随意改名libsession_manager_service或libsms。BMS401实际等待SA511并建目录失败，下一步是原installs服务。','18:50–18:52'),
 '系统截图':('已保存实际扫描缓冲PNG3048×2032；默认snapshot_display API仍2032×3048纯黑。推断捕获默认空显示节点与独立boot动画节点不同，需后续窗口/SceneBoard验证。','18:48'),
 '调试终端':('当前在Recovery，用ADB；重启v44/45 Probe后才用COM21。已停止动画/临时应用框架测试，摄像头关闭。','18:52:34')}
for c in r['Components']:
 if c['Name'] in u:c['State'],c['VerifiedAt']=u[c['Name']]
r['Components'].append({'Name':'可重复补丁与候选','State':'output/sheng-next-display-patch-v2.zip，含两模块完整SHA/guard工具及小型Vulkan适配源码/产物。v45仅离线候选，新增原installs/SA511门控及读回工具，未验收。','VerifiedAt':'18:53'})
r['Passed']=['v44已实刷冷启动：SHA守卫Rosen handle修正自动生效，原Turnip v1保留；不再手工下发DSo，双平面fb66和原composer提交记录通过。',
 '用户此前确认真实诊断图。v44再通过只读KMS GETFB2/PRIME DMA_BUF同步读回，原GPU像素3048×2032横屏完整；保留PPM gzip原始数据及SHA，PNG转换不改像素。',
 '默认snapshot_display API抓帧真实执行，回传SHA和逐像素统计确认全黑。没有把扫描读回或图片素材冒充默认截图API/桌面。',
 '通用守卫补丁v2生成；EOF和handle标志模块通过通用工具在新文件上重现已验收SHA，原文件不覆盖。',
 '原native foundation应用框架限时15秒测试加载401/180/501/182/3299及4607；真实日志定位BMS等待SA511、CreateBmsServiceDir失败10027408。恢复原4607单服务后已回Recovery，ADB root、版本/内核确认。',
 '原包installs.json准确对应SA511/libinstalls.z.so。离线v45加入原UID/GID/caps/kernel_permission/secon的显式门控，诊断禁cgroup记账、run-on-create=true；8MiB/LZ4/完整资产/原init保存验证通过，未刷入。']
r['Unfinished']=['桌面、触摸、窗口会话/SceneBoard、应用框架完整启动尚未完成，WiFi未开始，Zink未实测。',
 '默认截图API黑图/逻辑旋转仍未修好；仅实际扫描读回图已经成功。',
 'v45未刷/未运行，SA511没有通过。不能把库OpenSo成功称为401/180/501/182/3299全部服务发布。',
 '原composer可选ClientTargetProperty空指针、色彩metadata失败、非致命KGSL WARN仍需后续vendor功能适配；当前只确认本轮诊断显示链。',
 'metadata导出185234包含既有日志，Probe曾报persistent unavailable；本轮实际主证据是电脑COM日志、完整hilog gzip和截图文件，均已保留。']
r['Next']=['从已在Recovery的状态开始。优先刷预构建v45/ShengExports，SHA7136bd72739c4eadbca42b9e785cc3879447034f0d431d90c46e0cc994a3ee3c；当前源码已v45，不要用旧builder重编v44来回退，使用既有已校验镜像。',
 '先验收v45原显示冷启动基线，然后显式param sheng.debug.start.installs=true，验证原SA511发布和真实身份；不直接启动全套原init服务。',
 'SA511可用后才限时切foundation-app-core.json（401/180/501/182/3299/4607）重启原foundation角色，读取BMS/AMS/AppMgr实际错误，再逐步接appspawn和SceneBoard。不能把libsms任意重命名为libwms。',
 '方向：hilog有SetScreenCorrection screenRotation3、AddOrUpdateUserDisplayNode userId0无效及RSUIContext为空，作为后续默认截图/窗口排查线索，避免重新改已验收的双平面/DSC。',
 '每轮完整写状态，保留原包/真实userdata，允许修改工作副本与vendor；无commit/push。重启卡fastboot先恢复原机三启动镜像再Recovery。摄像头使用后立即关闭。']
r['Evidence']+=['output/logs/20261027-183711','output/logs/command-shell-20261027-183912-771ee4975603.log（v44冷启动fb66）','analysis/v44-native-screenshot-verification.json','output/screenshots/v44-cold-api-20261027-1840.jpeg','output/logs/command-shell-20261027-184124-e6eb283644fb.log（legacy WMS不在原包）','compat/sheng-framework/foundation-app-core-v1.json','output/logs/command-shell-20261027-184754-416bc0275676.log（KMS实际读回）','analysis/v44-scanout-capture-verification.json','output/screenshots/v44-actual-scanout-20261027-1848.ppm.gz','output/screenshots/v44-actual-scanout-20261027-1848.png','output/logs/command-shell-20261027-185001-5f0326ec52e5.log（限时应用框架测试/恢复）','output/logs/v44-hilog-20261027-1852.txt.gz（完整hilog，SHA9a3296bff66ec03495008d0ad6cf7b5504249bb6e4a4392e2c46200128dae36a）','output/logs/20261027-185234','analysis/portable-display-patch-v2.json','output/sheng-next-display-patch-v2.zip','analysis/v45-native-inputs.json','analysis/v45-image-verification.json','output/v45-manifest.json']
out=r0/'analysis/round-20261027-1855.json';out.write_text(json.dumps(r,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
subprocess.run(['pwsh','-NoProfile','-File',str(r0/'output/Save-RoundSummary.ps1'),'-RecordPath',str(out)],check=True)
banner='**'+datetime.now().strftime('%H:%M')+'最新交接：'+r['DeviceState']+' v45仅离线候选，下一步原installs/SA511，详见round-20261027-1855.json。之前卡Mi/无GPU是历史；默认API黑图仍是现实，勿混淆。已询问下一续接时间，未收到选择时不新建任务。**'
p=r0/'analysis/续接检查点.md';p.write_text(banner+'\n\n'+p.read_text(encoding='utf-8'),encoding='utf-8')
with (r0/'analysis/20261027续接进展.md').open('a',encoding='utf-8') as f:f.write('\n\n## '+datetime.now().strftime('%H:%M')+' v44冷启动/真实横屏读回/Recovery善后\n\n'+banner+'\n\n下一阻点证据：完整hilog行5902–5993，BMS重复等待SA511，CreateBmsServiceDir ret10027408。原installs.json name511，run-on-create=false，cfg service为installs。v45仅为此下一步而构建，未实刷。\n')
