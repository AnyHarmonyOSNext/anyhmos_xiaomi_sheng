from pathlib import Path
import json,subprocess
rdir=Path(__file__).resolve().parent.parent
r=json.loads((rdir/'analysis/round-20261027-1145.json').read_text(encoding='utf-8'))
r.update(Title='v38首屏无USB接口，已请求人工回fastboot；离线准备原LZ4容器候选',DeviceState='v38已刷入，停Mi首屏。11:50电脑无COM/ADB/fastboot，无法远程控制；摄像头已关闭。已异步请求方便时长按进fastboot，不能宣称当前Recovery可读。',Version='实际已刷Probe v38，a50aa4b3d02643e523dec933473009382e49efa8d572b4d9f69af39d06ba3ebc；当前无控制接口，冷启动未通过。v37是已验证回退包。')
for c in r['Components']:
    if c['Name']=='电脑连接':c.update(State='无COM/ADB/fastboot，首屏Mi；不能远程发reboot。等待用户方便时强制重启进入fastboot。',VerifiedAt='11:50')
    if c['Name']=='鸿蒙init和核心服务':c.update(State='v37冷启动五服务已通过；当前v38未确认init执行，不能沿用为当前运行。',VerifiedAt='当前未验收')
    if c['Name']=='GPU':c.update(State='v37手动加载303原KGSL成功建立493:0节点，device_links_driver_bound有WARN；未验证渲染。Turnip已交叉构建，v38携带但启动失败，GPU程序未执行。',VerifiedAt='11:46–11:50')
r['Passed']+=['Turnip固定Mesa提交和两个参考补丁交叉构建完成，原OHOS libc++ ABI、实际libsurface/hilog链接，AArch64 ELF依赖已记录。','v38构建/解包与全部原CPIO条目校验通过，但真实启动失败；两者严格区分。']
r['Unfinished']+=['v38首屏无USB，需人工强制重启进fastboot；自动恢复不可执行。','v38把整个ramdisk改为gzip；虽然精确内核CONFIG_RD_GZIP=y、镜像解包通过，尚不能确定是否启动回归原因。候选v39保留原LZ4容器，仅GPU数据gzip打包。']
r['Next']=['人工回fastboot后先完整恢复原机boot/vendor_boot/init_boot，再回TWRP、导出metadata日志；不能跳过用户规定。','离线构建校验v39：原LZ4容器＋GPU压缩数据，不提前称通过或自动刷写。','离线继续Zink和GPU契约准备，等待设备恢复后执行真实GPU像素读回。']
r['Evidence']+=['output/logs/20261027-114853','analysis/v38-image-verification.json','output/v38-manifest.json','analysis/sheng-gpu-v1-build.json','output/camera/20261027-115025-v38-boot-state/exposure-3_0.jpg','output/logs/command-shell-20261027-114640-f925a6dd22c6.log']
out=rdir/'analysis/round-20261027-1151.json';out.write_text(json.dumps(r,ensure_ascii=False,indent=2)+'\n',encoding='utf-8');subprocess.run(['pwsh','-NoProfile','-File',str(rdir/'output/Save-RoundSummary.ps1'),'-RecordPath',str(out)],check=True)
p=rdir/'analysis/续接检查点.md';text='**11:51最新：v38真实启动失败，Mi首屏、无COM/ADB/fastboot，已请求用户方便时强制重启进fastboot。此时必须先完整恢复原机三启动镜像再进TWRP/收日志。不能声称设备已在Recovery。v37及HDI远程帧物理验收为已通过回退基线。v39离线候选保留原LZ4容器，仅GPU数据gzip，无真机结论。摄像头释放。**';p.write_text(text+'\n\n'+p.read_text(encoding='utf-8'),encoding='utf-8')
with (rdir/'analysis/20261027续接进展.md').open('a',encoding='utf-8') as f:f.write('\n\n## 11:51 v38启动回归\n\n'+text+'\n\nMesa Turnip ce6413a25a0fb8cf3cf3d58a0026e506889ab171435b34eb2bc383e6d29503d9，9336672字节，gzip1819513。v38原ramdisk整体gzip6642446字节，镜像8MiB解包逐字节校验通过但无USB/首屏Mi。内核CONFIG_RD_GZIP=y不能替代真机验收；启动回归原因未证实。v37实际原303 msm_kgsl位于/hmos-root/vendor_dlkm/lib/modules，sha567595f1a27f44936042e94fcdbc2578798f7e3cca839f68180cfbc3130e2d93，加载节点493:0，出现device_links_driver_bound WARN，未GPU渲染。重启前日志已导出114853。\n')
