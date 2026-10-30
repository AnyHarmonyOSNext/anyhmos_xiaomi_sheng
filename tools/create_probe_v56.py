"""Add missing original desktop services and global storage initialization."""
from pathlib import Path
import shutil,json,subprocess
r=Path(__file__).resolve().parent.parent
for name in ['hmos_probe.c','probe_graphics.inc','probe_command.inc']:
    p=r/'tools'/name;dst=r/'tools/archive'/(p.stem+'_v55'+p.suffix)
    if not dst.exists():shutil.copy2(p,dst)
d=r/'compat/sheng-graphics/v56'
assert not d.exists()
shutil.copytree(r/'compat/sheng-graphics/v55',d)
sdk='/root/hmos-work/sdk-6.0.0.47/installed/native/llvm/bin/'
w='/mnt/c/SHENG_WORKSPACE/'
subprocess.run(['wsl','-d','Ubuntu-22.04','-u','root','--',sdk+'clang','--target=aarch64-linux-ohos','-O2','-Wall','-Wextra','-Werror','-shared','-fPIC','-Wl,-z,relro,-z,now',w+'compat/sheng-framework/persistent-v1/el5_unavailable.c','-o',w+'compat/sheng-graphics/v56/libsheng_el5_unavailable.so'],check=True)
subprocess.run(['wsl','-d','Ubuntu-22.04','-u','root','--',sdk+'llvm-strip',w+'compat/sheng-graphics/v56/libsheng_el5_unavailable.so'],check=True)
cfg=json.loads((r/'tools/configs/init-core-v55.cfg').read_text())
pre=next(j for j in cfg['jobs'] if j['name']=='pre-init')['cmds']
pre[0:0]=[f'mkdir /data/{base} 0711 root root' for base in ['service','chipset','app','misc']]
next(s for s in cfg['services'] if s['name']=='installs')['env']=[{'name':'LD_PRELOAD','value':'/compat/lib64/libsheng_el5_unavailable.so'}]
(r/'tools/configs/init-core-v56.cfg').write_bytes((json.dumps(cfg,indent=2)+'\n').encode())
extra=json.loads((d/'init-desktop-services.cfg').read_text())
extra['jobs'].append({'name':'param:sheng-init-main-user','condition':'sheng.debug.init.mainuser=true','cmds':['exec /system/bin/sdc filecrypt init_main_user']})
for filename,name,gate in [('themeManagerServer.cfg','theme_manager_service','theme'),('wallpaperservice.cfg','wallpaper_service','wallpaper')]:
    original=json.loads((r/'work/hmos_system/system/system/etc/init'/filename).read_text())
    s=next(x for x in original['services'] if x['name']==name)
    for key in ['critical','writepid','jobs','on-restart','ondemand']:s.pop(key,None)
    s.update(disabled=1,once=1,saspawn=False);s['start-mode']='condition'
    extra['services'].append(s)
    cmds=[c for j in original.get('jobs',[]) for c in j['cmds'] if c.startswith('mkdir ')]
    extra['jobs'].append({'name':'param:sheng-debug-'+gate,'condition':'sheng.debug.start.'+gate+'=true','cmds':cmds+['start '+name]})
(d/'init-desktop-services.cfg').write_bytes((json.dumps(extra,indent=2)+'\n').encode())
profile=json.loads((d/'foundation-app-core.json').read_text())
orig=json.loads((r/'work/hmos_system/system/system/profile/foundation.json').read_text())
profile['systemability'] += [s for s in orig['systemability'] if s['name'] in [4606,3704]]
(d/'foundation-app-core.json').write_bytes((json.dumps(profile,indent=2)+'\n').encode())
p=r/'tools/probe_graphics.inc';s=p.read_text()
mark='    if(copy_ram_asset("/graphics/libsheng_ram_no_tee.so"'
assert s.count(mark)==1
s=s.replace(mark,'    if(copy_ram_asset("/graphics/libsheng_el5_unavailable.so","/hmos-root/compat/lib64/libsheng_el5_unavailable.so",0644)<0)return -1;\n'+mark)
p.write_text(s)
p=r/'tools/hmos_probe.c';s=p.read_text().replace('v55','v56')
mark='static void trace_handoff(int kind) {\n    if(getpid()!=1)return;'
assert s.count(mark)==1
s=s.replace(mark,mark+'\n    if(kind!=0&&access("/sys/module/sheng_hmos_ipc",F_OK)<0){note("HMOS handoff rejected: load the verified IPC module first with ipc");return;}')
p.write_text(s)
for name in ['build_probe','verify']:
    s=(r/f'tools/{name}_v55.py').read_text().replace('v55','v56')
    if name=='verify':
        s=s.replace("=={'storage_daemon','storage_manager','distributeddata'}","=={'storage_daemon','storage_manager','distributeddata','theme_manager_service','wallpaper_service'}")
        s=s.replace(" assert len(new['hmos-init-debug.cfg'][1])<32768"," assert 'graphics/libsheng_el5_unavailable.so' in new\n assert len(new['hmos-init-debug.cfg'][1])<32768")
    (r/f'tools/{name}_v56.py').write_text(s)
print('v56 staged: global init gate, complete parents, WMS/screenlock, theme/wallpaper, absent EL5 returns failure immediately')
