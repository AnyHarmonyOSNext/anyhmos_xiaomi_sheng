"""Full honest handoff when USB recovery needs a physical button action."""
from pathlib import Path
from datetime import datetime
import json,subprocess
root=Path(__file__).resolve().parent.parent
now=datetime.now();tag=now.strftime('%Y%m%d-%H%M')
r=json.loads((root/'analysis/round-20261027-1151.json').read_text(encoding='utf-8'))
r.update(Title='待人工恢复USB；v39及Turnip/Zink离线准备完成',DeviceState='设备仍停Mi首屏，电脑无COM/ADB/fastboot；无法远程进入Recovery，已异步请求方便时长按进入fastboot。没有正在运行的刷写/串口/构建/摄像头进程。不能宣称已完成本次回TWRP善后。',Version='实际已刷v38且冷启动失败；已通过回退基线v37。候选v39仅构建/解包/原CPIO及LZ4边界/Turnip gzip还原校验通过，未刷入。v39 Probe SHA256 4df9e00d3083cfcbb789d5a2faef2dead2aa83a13e349899f7fc966e2be8a36f；8MiB。',Kernel='已刷boot镜像为ShengExports 5.15.178-android13-8-00021-g6f2f96be86b9-ab13729987；当前无接口，不能读取实际运行uname。原CFI/KMI验证保留，Recovery5.15.144禁止加载该版本模块。',QuotaPolicy='最近实查本窗口已用19%、remaining81%、ordinaryUsageAllowed=true，并非额度不足停止；当前真机测试受物理恢复USB阻塞。近额度2%–3%善后/1%停止规则继续保留。11:35单次续接已执行并删除id=automation，未安排重复任务；未来新续接需按用户授权和真实重置时间。')
for c in r['Components']:
    name=c['Name']
    if name=='当前内核':c.update(State=r['Kernel'],VerifiedAt='镜像已刷；当前运行未读')
    if name=='GPU':c.update(State='Turnip和Zink均已按Mesa ea74a63399交叉构建，原OHOS平台ABI，实际DSO依赖和哈希有报告；尚无GPU shader/像素读回真机结果。v39只携带Turnip和两个契约，Zink未打包。',VerifiedAt='本轮离线构建；非真机通过')
    if name=='桌面 / 窗口 / RenderService':c.update(State='尚未启动桌面；历史只有UID0 8秒诊断。SA3901/1912原profile已提取核实；原UID/权限/显式条件启动候选已准备，未打包/执行。',VerifiedAt='本轮离线准备；尚待真机')
    if name=='调试终端':c.update(State='当前无USB接口。摄像头最近一次capture released=true，无WindowsCamera/后台摄像头/串口进程。',VerifiedAt=now.strftime('%H:%M'))
r['Passed']+=['v39保留stock vendor legacy-LZ4容器，仅Turnip二进制作为gzip数据；所有原CPIO条目和原init保留、8MiB镜像及资产逐字节校验通过，未刷入。','Zink EGL/GLES/gallium和EGL GPU契约已离线交叉构建/strip，AArch64、NEEDED和哈希记录完整；未真机加载。','已提取核实原param_watcher=SA3901及concurrent_task_service=SA1912，准备8727字节原生UID/GID/权限候选配置；没有启动或注册成功结论。','11:35单次automation已执行并删除，没有重复计划。']
r['Unfinished']=[s for s in r['Unfinished'] if 'v38把整个' not in s]
r['Unfinished']+=['离线已发现mixed压缩边界风险：vendor legacy-LZ4无零终止，若直接拼接generic gzip会被同一unlz4循环当成LZ4块；这是强线索，真实失败原因仍待恢复后日志证实。','v39冷启动、Turnip真GPU shader/显式同步/像素guard读回、Zink/EGL均未实测；不能把交叉编译或色条称GPU/桌面成功。','本次新启动v38日志尚未能导出，最近完整metadata导出是重启前output/logs/20261027-114853。']
r['Next']=['用户方便时长按强制重启进入fastboot并保持USB；先完整03-Restore-BootChain恢复该设备备份boot/vendor_boot/init_boot，再fastboot reboot recovery。不临时boot未知镜像。','TWRP ADB root后先02-Collect-Recovery导出v38启动日志，确认实际失败点；恢复前不能写新试验覆盖线索。','随后可显式01-Flash-Probe -Serial YOUR_DEVICE_SERIAL -Version v39 -Kernel ShengExports：先冷启动核实串口、ipc、hmos/五服务，再解出RAM GPU库并核SHA，加载原303 GPU模块和真实sysfs字符节点，执行限时native_buffer_contract。','Turnip原生像素/同步契约通过后，才接入原Vulkan loader及RenderService原UID的SA3901/1912依赖候选；真实displayId建立后系统截图。','Zink是独立离线载荷，未包含v39；后续部署保留SONAME别名和gallium依赖。已通过HDI远程帧/Binder/token基本契约无需重复。']
r['Evidence']+=['analysis/v39-image-verification.json','output/v39-manifest.json','analysis/ramdisk-container-preflight.json','tools/check_ramdisk_container.py','analysis/sheng-zink-v1-build.json','compat/sheng-graphics/zink-v1','analysis/next-native-service-inputs.json','compat/sheng-framework/next-native-services/README.md','work/zink-build-1156.log']
out=root/f'analysis/round-{tag}-offline.json';out.write_text(json.dumps(r,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
subprocess.run(['pwsh','-NoProfile','-File',str(root/'output/Save-RoundSummary.ps1'),'-RecordPath',str(out)],check=True)
banner='**'+now.strftime('%H:%M')+'最新交接：v38停Mi首屏无COM/ADB/fastboot，等待用户方便时强制重启进fastboot；此后必须先恢复原机boot/vendor_boot/init_boot三者，再TWRP/收日志。不能声称当前在Recovery。v37/HDI远程帧物理验收已通过；v39仅构建解包/LZ4容器校验，SHA256 4df9e00d3083cfcbb789d5a2faef2dead2aa83a13e349899f7fc966e2be8a36f。Turnip/Zink已构建，但GPU渲染/桌面/系统截图均未通过。最近导出日志114853；新v38日志未取。摄像头已释放，无并发控制器。额度剩81%，本次受物理恢复阻塞；11:35单次任务已执行并删除automation，无新安排。完整状态'+out.name+'。**'
p=root/'analysis/续接检查点.md';p.write_text(banner+'\n\n'+p.read_text(encoding='utf-8'),encoding='utf-8')
with (root/'analysis/20261027续接进展.md').open('a',encoding='utf-8') as f:f.write('\n\n## '+now.strftime('%H:%M')+' 离线交接与设备恢复阻塞\n\n'+banner+'\n\n格式证据：原vendor_ramdisk30994054字节，单一LZ4 legacy档案9个块，无零终止；kernel lib/decompress_unlz4.c会接受下一LZ4魔数，不能把gzip开头当新类型自动切换（如果bootloader直接拼接）。v38为gzip6642446，v39恢复LZ4 7406420。明确为离线强线索，不冒充本机kernel日志。Zink产物libgallium14380440字节，EGL317080，GLESv2 54568，真实依赖/哈希在sheng-zink-v1-build.json。新服务候选保持原native身份/权限并增加graphics组用于新KGSL/DRM节点；未打包、未启动。\n')
print(out)
