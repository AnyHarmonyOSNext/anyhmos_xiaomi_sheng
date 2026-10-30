"""Offline staged config only: preserve native identities, explicit start gates."""
from pathlib import Path
import json,hashlib
r=Path(__file__).resolve().parent.parent
cfg=r/'work/hmos_system/system/system/etc/init'
out=r/'compat/sheng-framework/next-native-services';out.mkdir(parents=True,exist_ok=True)
core=json.loads((r/'tools/configs/init-core-v39.cfg').read_text())
original=[]
for file,name in [('param_watcher.cfg','param_watcher'),('concurrent_task_service.cfg','concurrent_task_service'),('graphic.cfg','render_service')]:
    data=json.loads((cfg/file).read_text())
    service=next(s for s in data['services'] if s['name']==name)
    original.append({'name':name,'file':file,'source_sha256':hashlib.sha256((cfg/file).read_bytes()).hexdigest(),'uid':service['uid'],'gid':service.get('gid'),'permission':service.get('permission',[])})
    service={k:v for k,v in service.items() if k not in ['critical','jobs','writepid']}
    service.update({'disabled':1,'once':1,'start-mode':'condition','sandbox':0})
    if name=='render_service' and 'graphics' not in service['gid']:
        # Added SM8550 KGSL/DRM group; original native UID and groups retained.
        service['gid'].append('graphics')
    core['services'].append(service)
    if name=='render_service':
        # Only original directory setup is retained; every /data path is RAM.
        for job in data['jobs']:
            if job['name'] in ['init','post-fs-data']:
                cmds=[c for c in job['cmds'] if c.startswith('mkdir /data/')]
                core['jobs'].append({'name':'sheng-render-'+job['name'],'cmds':cmds})
core['jobs'] += [
 {'name':'param:sheng-debug-coredeps','condition':'sheng.debug.start.coredeps=true','cmds':['start param_watcher','start concurrent_task_service']},
 {'name':'param:sheng-debug-render','condition':'sheng.debug.start.render=true','cmds':['trigger sheng-render-init','trigger sheng-render-post-fs-data','setparam persist.rosen.disableddgr.enabled 1','start render_service']}]
encoded=(json.dumps(core,ensure_ascii=False,indent=2)+'\n').encode();assert len(encoded)<16384
assert len(core['services'])==8 and all('critical' not in s and s['once']==1 for s in core['services'])
(out/'init-core-next.cfg').write_bytes(encoded)
icd={'file_format_version':'1.0.0','ICD':{'library_path':'/data/local/tmp/sheng-graphics/libvulkan_freedreno.so','api_version':'1.3.0'}}
(out/'sheng-turnip.json').write_text(json.dumps(icd,indent=2)+'\n')
(out/'README.md').write_text('''# 尚未真机验收的原生服务候选

此目录未打包、未刷入、未启动。保留原包 UID/原有 GID/权限/secon，并为 RenderService 增加 graphics 组以访问 SM8550 RAM KGSL/DRM 节点；删除 critical、原有 on-restart 联动和未提供的 Android cgroup writepid，设置 condition/disabled/once。不能称原生服务已验证。

`sheng.debug.start.coredeps=true` 才启动 param_watcher SA3901、concurrent_task_service SA1912。`sheng.debug.start.render=true` 才建原图形 RAM 目录并启动 RenderService。测试后须 stop 并核对残留进程；不得依赖关键服务重启整机。

前置条件：原 KGSL 模块和 RAM 字符节点、gzip 解出 Turnip 并 SHA 验证。v39冷启动、shader/同步/像素读回及原生Rosen像素读回已通过；本机原loader忽略VK_ICD_FILENAMES，必须在RAM vendor overlay的原vulkan_driver_v350.json使用Turnip配置。RAM参数persist.rosen.disableddgr.enabled=1使原生模式变量自行选择Vulkan1，已用无全局变量覆盖的rosen_native_mode验收通过。root契约不代替原UID服务验收。

所有 /data 均为现有 RAM tmpfs，实际 userdata 不接入。显示对象和窗口创建后再尝试 snapshot_display；此配置并未启动 foundation/桌面。
''',encoding='utf-8')
(r/'analysis/next-native-service-inputs.json').write_text(json.dumps({'status':'offline_candidate_unbuilt_unflashed','config_bytes':len(encoded),'config_sha256':hashlib.sha256(encoded).hexdigest(),'native_services':original},ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print('Native-service offline config bytes:',len(encoded))
