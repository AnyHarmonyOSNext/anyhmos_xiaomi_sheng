from pathlib import Path
import json,subprocess
root=Path(__file__).resolve().parent.parent
r=json.loads((root/'analysis/round-20261027-0800.json').read_text(encoding='utf-8-sig'))
r.update(Title='v37冷启动通过：自动ashmem节点和原HDI SMQ请求回复',DeviceState='YOUR_DEVICE_SERIAL现运行Probe v37 + ShengExports，COM21可读，原鸿蒙init及五个核心服务正常；尚未进入桌面。',Version='已刷入并冷启动通过Probe v37，SHA256 7cb03afbb844ec784ca60ae1bb32a560d3ca48fea70b6fd716786ebf2ae59fad；boot为ShengExports，vendor_boot原303。',Kernel='Probe当前为5.15.178-android13-8-00021-g6f2f96be86b9-ab13729987；精确Google common提交6f2f96be86b93de6ed58a2c46b456fb49734c382，CFI与原KMI CRC保留。',QuotaPolicy='11:35额度已重置且ordinaryUsageAllowed=true；11:39使用5%，本窗口按2%–3%开始善后、1%停止。11:35一次性续接正在执行，未另建重复任务。')
updates={
'电脑连接':('COM21可读；11:35起先核对Recovery与无冲突进程，再串行刷v37/加载ipc/启动hmos。','11:35–11:40'),
'当前内核':(r['Kernel'],'11:37冷启动'),
'鸿蒙init和核心服务':('原init第二阶段，hilogd1036/samgr5555/hdf_devmgr3044/allocator_host3041/composer_host3036均在运行。','11:40'),
'HDF图形服务':('v37自动ashmem10:127/0666，本地SMQ读写、原代理InitCmdRequest/GetCmdReply均0。尚未验收远程帧提交。','11:40冷启动'),
'GPU':('此前v25仅Adreno740原模块open通过；当前v37未加载GPU，尚未验证GPU渲染。','历史结果；待本轮推进')}
for c in r['Components']:
    if c['Name'] in updates:c['State'],c['VerifiedAt']=updates[c['Name']]
r['Passed']=['v37真实刷入和冷启动完成，随包ashmem节点自动创建，五个原生核心服务运行。','SMQ本地读写和原HDI代理请求/回复通过，无需手动补节点；HDI_SMQ_RESULT=0。','先前v36双平面/完整PowerOFF重建验收保留，本轮未重复Binder/token或色条合约。']
r['Unfinished']=[x for x in r['Unfinished'] if 'v37增加' not in x]
r['Next']=['通过原生HDI高层客户端提交真实帧，验证SMQ/FD/缓存传递到服务端的完整链路。','推进Turnip/Zink用户态、原生RenderService和缺失系统服务；真实displayId建立后再截系统图。','每轮完整总结，单一设备控制器，摄像头立即释放；额度近限时回TWRP导出日志。']
r['Evidence']=['output/v37-manifest.json','analysis/v37-image-verification.json','output/logs/command-ipc-20261027-113658.log','output/logs/command-hmos-20261027-113943.log','output/logs/command-shell-20261027-114006-bc09c3b63f39.log','analysis/round-20261027-0800.json（此前证据索引）']
out=root/'analysis/round-20261027-1140.json';out.write_text(json.dumps(r,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
subprocess.run(['pwsh','-NoProfile','-File',str(root/'output/Save-RoundSummary.ps1'),'-RecordPath',str(out)],check=True)
p=root/'analysis/续接检查点.md';old=p.read_text(encoding='utf-8-sig');p.write_text('**11:40最新：Probe v37已刷入并冷启动通过；COM21可读，原init和五服务运行，ashmem10:127/0666自动创建，原HDI SMQ本地读写/请求/回复全部成功。接下来推进远程帧提交、GPU用户态和RenderService；尚无桌面或系统截图。见当前状态.md及round-20261027-1140.json。11:35续接正在执行，以下08:00为历史。**\n\n'+old,encoding='utf-8')
with (root/'analysis/20261027续接进展.md').open('a',encoding='utf-8') as f:f.write('\n\n## 11:40 v37冷启动\n\nv37实刷成功，五服务和自动ashmem节点、原HDI SMQ读写/请求/回复通过，证据command-shell-20261027-114006-bc09c3b63f39.log。尚未测试远程帧提交，未启动桌面。先前Binder/token与显示基线不重复。额度已重置允许运行。\n')
