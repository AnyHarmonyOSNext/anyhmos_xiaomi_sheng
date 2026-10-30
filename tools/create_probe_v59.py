"""Keep WiFi explicitly unavailable to SceneBoard without blocking its UI."""
from pathlib import Path
import shutil,json,subprocess
r=Path(__file__).resolve().parent.parent
for n in ['hmos_probe.c','probe_graphics.inc','probe_command.inc']:
 p=r/'tools'/n;q=r/'tools/archive'/(p.stem+'_v58'+p.suffix)
 if not q.exists():shutil.copy2(p,q)
d=r/'compat/sheng-graphics/v59'
# v58's original WiFi manager was unable to remain running without chip HDI.
shutil.copytree(r/'compat/sheng-graphics/v57',d,dirs_exist_ok=True)
cfg=json.loads((r/'tools/configs/init-core-v57.cfg').read_text())
next(x for x in cfg['services'] if x['name']=='appspawn')['env']=[{'name':'LD_PRELOAD','value':'/compat/lib64/libsheng_wifi_ui_unavailable.so'}]
(r/'tools/configs/init-core-v59.cfg').write_text(json.dumps(cfg,indent=2)+'\n')
w='/mnt/c/SHENG_WORKSPACE/'
sdk='/root/hmos-work/sdk-6.0.0.47/installed/native/llvm/bin/'
subprocess.run(['wsl','-d','Ubuntu-22.04','-u','root','--',sdk+'clang','--target=aarch64-linux-ohos','-O2','-Wall','-Wextra','-Werror','-shared','-fPIC','-Wl,-z,relro,-z,now',w+'compat/sheng-framework/persistent-v1/wifi_ui_unavailable.c','-o',w+'compat/sheng-graphics/v59/libsheng_wifi_ui_unavailable.so'],check=True)
subprocess.run(['wsl','-d','Ubuntu-22.04','-u','root','--',sdk+'llvm-strip',w+'compat/sheng-graphics/v59/libsheng_wifi_ui_unavailable.so'],check=True)
p=r/'tools/hmos_probe.c';p.write_text(p.read_text().replace('v58','v59'))
p=r/'tools/probe_graphics.inc';s=p.read_text().replace('v58','v59')
mark='    if(copy_ram_asset("/graphics/libsheng_el5_unavailable.so","/hmos-root/compat/lib64/libsheng_el5_unavailable.so",0644)<0)return -1;'
assert s.count(mark)==1
s=s.replace(mark,mark+'\n    if(copy_ram_asset("/graphics/libsheng_wifi_ui_unavailable.so","/hmos-root/compat/lib64/libsheng_wifi_ui_unavailable.so",0644)<0)return -1;')
p.write_text(s)
for n in ['build_probe','verify']:
 (r/f'tools/{n}_v59.py').write_text((r/f'tools/{n}_v57.py').read_text().replace('v57','v59'))
print('v59 scoped WiFi unavailable fallback; original service omitted')
