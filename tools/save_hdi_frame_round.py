from pathlib import Path
import json,subprocess
root=Path(__file__).resolve().parent.parent
r=json.loads((root/'analysis/round-20261027-1140.json').read_text(encoding='utf-8'))
r['Title']='原HDI远程帧提交和完整物理出图验收通过'
for c in r['Components']:
    if c['Name']=='HDF图形服务':c.update(State='原厂IDisplayBuffer和IDisplayComposerInterface1.3，真实allocator Binder/DMABUF FD/SMQ缓存/服务端VDI，28次双缓冲提交、两次OFF/ON均成功。摄像头在第二次重亮后确认全屏图案。',VerifiedAt='11:44–11:45')
r['Passed']+=['原HDI高层客户端真实分配两块buffer，通过原生SMQ和FD传递进行28次换帧、两次关屏重亮，exit0。','11:44:58同步短时实拍显示满屏完整新图案；camera finally released=true。此前两张拍晚至测试关闭后的黑屏不计显示失败。']
r['Unfinished']=[s.replace('HDI远程帧提交、','') for s in r['Unfinished']]
r['Next']=['推进原303 KGSL模块与Turnip/Zink GPU用户态；Mesa固定ea74a63399及参考补丁正在私有树交叉构建。','推进原生RenderService和SA3901/1912等依赖，真实显示对象建立后系统截图。','每轮记录及额度善后规则不变，不重复Binder/token/帧传输已通过基线。']
r['Evidence']+=['analysis/hdi-frame-v2-build.json','tools/sheng_hdi_scanout.cpp','output/logs/command-shell-20261027-114437-5569e583106a.log','output/camera/20261027-114458-hdi-remote-confirmed-active/exposure-3_0.jpg','output/camera/20261027-114458-hdi-remote-confirmed-active/capture.json']
out=root/'analysis/round-20261027-1145.json';out.write_text(json.dumps(r,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
subprocess.run(['pwsh','-NoProfile','-File',str(root/'output/Save-RoundSummary.ps1'),'-RecordPath',str(out)],check=True)
text='**11:45最新：原HDI allocator/DMABUF FD/SMQ/composer远程帧完整通过，28次换帧、两次关屏重亮，第二次重亮后的摄像头全屏图案实拍通过并立即释放。v37冷启动五服务/ashmem通过；尚无桌面、GPU渲染或系统截图。正构建私有Turnip用户态。详见round-20261027-1145.json。**'
p=root/'analysis/续接检查点.md';p.write_text(text+'\n\n'+p.read_text(encoding='utf-8'),encoding='utf-8')
with (root/'analysis/20261027续接进展.md').open('a',encoding='utf-8') as f:f.write('\n\n## 11:45 原HDI远程帧提交\n\n'+text+'\n\n客户端tools/sheng_hdi_scanout.cpp：原包libdisplay_composer_hdi_impl_1.3.z.so和libdisplay_buffer_hdi_impl.z.so真实接口；AllocMem/Mmap/Invalidate/FlushCache，两块不同图案buffer，seqNo0/1缓存，SMQ SetDisplayClientBuffer/Commit28次，OFF/ON两次，再PowerOFF/释放。不能称GPU渲染或桌面截图。证据command-shell-20261027-114437-5569e583106a.log及camera/20261027-114458-hdi-remote-confirmed-active。Mesa源码固定ea74a6339917390657db153cb9792f9ccac9f5ae，参考两补丁仅应用私有工作树，无commit/push。\n')
