from pathlib import Path
from datetime import datetime
import json,subprocess
root=Path(__file__).resolve().parent.parent;now=datetime.now()
r=json.loads((root/'analysis/round-20261027-1159-offline.json').read_text(encoding='utf-8'))
r.update(Title='恢复完成；v39冷启动及真实Turnip shader读回通过',DeviceState='YOUR_DEVICE_SERIAL已先完整恢复原机boot/init_boot/vendor_boot，成功进入TWRP并确认ADB root、导出日志161605；随后显式刷v39/ShengExports，COM21已恢复，五个核心服务运行。当前尚无鸿蒙桌面，Mi首屏仍保留。',Version='Probe v39已冷启动通过，SHA256 4df9e00d3083cfcbb789d5a2faef2dead2aa83a13e349899f7fc966e2be8a36f，A槽，原303 vendor_boot+ShengExports boot。',Kernel='当前Probe 5.15.178-android13-8-00021-g6f2f96be86b9-ab13729987，精确源码/原CFI/KMI保留；当前v39启动日志已核实。',QuotaPolicy='16:19实际额度已用25%，ordinaryUsageAllowed=true，本窗口16:35:37重置；剩2%–3%开始善后、1%停止规则保留。11:35一次性任务已执行并删除，无新安排。')
updates={
'电脑连接':('COM21已恢复，可读指令日志；恢复流程先完成原机三启动镜像回刷与TWRP/ADB root，未跳过。','16:15–16:18'),
'当前内核':(r['Kernel'],'v39冷启动日志'),
'鸿蒙init和核心服务':('原鸿蒙init第二阶段；hilogd1036/samgr5555/hdf_devmgr3044/allocator_host3041/composer_host3036，v39五服务在运行。','16:18'),
'GPU':('原303五模块SHA先核对，KGSL节点动态创建，Turnip GPU=Adreno740。真实shader12288像素读回全部正确、4096字节guard不变、acquire/release同步通过。参考契约使用原SurfaceBuffer+handle字段fixture，非allocator IPC验证，也非全屏输出。','16:18:35'),
'桌面 / 窗口 / RenderService':('Rosen契约返回GPU上下文对象，但MakeRenderTarget得到空surface、exit1；尚未通过Rosen绘图，原生RenderService/窗口/桌面均未启动。','16:19:20'),
'调试终端':('COM21恢复，单一串口控制器；本轮尚未使用摄像头。','16:18–16:19')}
for c in r['Components']:
    if c['Name'] in updates:c['State'],c['VerifiedAt']=updates[c['Name']]
r['Passed']=['用户恢复fastboot后，完整回刷实际备份三启动分区并成功回TWRP/ADB root；日志导出161605。未发现Probe v38标记的新日志，无法据此取得kernel失败栈。','v39恢复原LZ4 ramdisk后冷启动/COM21/五服务通过。v38 mixed容器是强回归线索，未取得其启动内核日志。','Turnip真实shader像素/guard/acquire-release同步契约exit0；GPU识别Turnip Adreno740。','原GPU模块device_links_driver_bound WARN仍出现但未阻止本轮shader通过；尚未定位并消除WARN。']
r['Unfinished']=['Rosen原生绘图契约MakeRenderTarget返回空，需读取hilog定位；不能只看nonnull GPU对象称绘图通过。','原UID1003的RenderService、SA3901/1912依赖、窗口/桌面、系统截图尚未通过。屏幕Mi图标是尚无桌面提交；本轮GPU是内存小图测试。','Zink仅离线编译；尚未部署验收。实际全屏GPU绘图尚未验收。']
r['Next']=['先解析Rosen/Vulkan错误，接通原loader，再跑原生Rosen像素读回。','推进显式条件启动的原native UID/权限依赖和RenderService；显示对象建立后尝试真实系统截图。','每轮完整记录，摄像头用完释放、单控制器、额度善后规则保持。']
r['Evidence']+=['output/logs/20261027-161605','output/logs/command-ipc-20261027-161754.log','output/logs/command-hmos-20261027-161804.log','output/logs/command-shell-20261027-161820-b5e842146ca5.log（CRLF脚本失败、未加载）','output/logs/command-shell-20261027-161835-2b4ae0f51184.log（修为LF，GPU真实shader通过）','output/logs/command-shell-20261027-161920-318053beb7e8.log（Rosen surface空）']
out=root/'analysis/round-20261027-1620.json';out.write_text(json.dumps(r,ensure_ascii=False,indent=2)+'\n',encoding='utf-8');subprocess.run(['pwsh','-NoProfile','-File',str(root/'output/Save-RoundSummary.ps1'),'-RecordPath',str(out)],check=True)
banner='**16:20最新：已按用户要求完整恢复原机三个启动镜像、进入TWRP/ADB root并导出161605。v39已实刷冷启动通过、COM21和五服务恢复。Turnip Adreno740真实shader12288像素/4096guard/acquire-release同步exit0。Rosen仅GPU对象nonnull，MakeRenderTarget surface为空exit1，未通过原生绘图；正抓hilog。还没有桌面或系统截图，Mi图标保留。详见round-20261027-1620.json。**'
p=root/'analysis/续接检查点.md';p.write_text(banner+'\n\n'+p.read_text(encoding='utf-8'),encoding='utf-8')
with (root/'analysis/20261027续接进展.md').open('a',encoding='utf-8') as f:f.write('\n\n## 16:20 v39冷启动和真实GPU\n\n'+banner+'\n\nLF脚本tools/prepare_gpu_device_script.py对5个原303模块SHA逐一核对后加载，sysfs动态创建RAM KGSL节点0:graphics0660，解出GPU库校验ce6413a...，native_buffer_contract真实shader/同步/guard通过。参考契约SurfaceBuffer手工handle fixture必须如实标注，不替代allocatorIPC。Rosen待修surface空。\n')
