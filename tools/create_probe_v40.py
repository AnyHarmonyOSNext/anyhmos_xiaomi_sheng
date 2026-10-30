"""Stage verified GPU loader config and explicitly gated native services."""
from pathlib import Path
import shutil,json,subprocess
r=Path(__file__).resolve().parent.parent
subprocess.run(['python','-X','utf8',str(r/'tools/prepare_next_native_services.py')],check=True)
for name in ['hmos_probe.c','probe_graphics.inc','probe_command.inc']:shutil.copy2(r/'tools'/name,r/'tools/archive'/(Path(name).stem+'_v39'+Path(name).suffix))
p=r/'tools/hmos_probe.c';p.write_text(p.read_text().replace('v39','v40'))
p=r/'tools/probe_graphics.inc';s=p.read_text().replace('"rosen_gpu_contract"','"rosen_gpu_contract","rosen_native_mode"')
needle='    DIR *firmware=opendir("/stock-gpu-firmware");'
assert needle in s
s=s.replace(needle,'    if(copy_ram_asset("/graphics/sheng-turnip.json","/hmos-root/vendor/etc/vulkan/icd.d/vulkan_driver_v350.json",0644)<0||\n       copy_ram_asset("/graphics/sheng-turnip.json","/hmos-root/data/local/tmp/sheng-turnip.json",0644)<0)return -1;\n'+needle)
p.write_text(s)
shutil.copy2(r/'compat/sheng-framework/next-native-services/init-core-next.cfg',r/'tools/configs/init-core-v40.cfg')
dst=r/'compat/sheng-graphics/v40';shutil.copytree(r/'compat/sheng-graphics/v39',dst,dirs_exist_ok=True)
shutil.copy2(r/'compat/sheng-graphics/rosen-native-mode-v1/rosen_native_mode',dst/'rosen_native_mode')
shutil.copy2(r/'compat/sheng-framework/next-native-services/sheng-turnip.json',dst/'sheng-turnip.json')
(r/'tools/build_probe_v40.py').write_text((r/'tools/build_probe_v39.py').read_text().replace('v39','v40'))
s=(r/'tools/verify_v39.py').read_text().replace('v39','v40')
s=s.replace("{'samgr','hilogd','hdf_devmgr','allocator_host','composer_host'}","{'samgr','hilogd','hdf_devmgr','allocator_host','composer_host','param_watcher','concurrent_task_service','render_service'}")
s=s.replace("config=json.loads(new['hmos-init-debug.cfg'][1]);", "config=json.loads(new['hmos-init-debug.cfg'][1]);")
(r/'tools/verify_v40.py').write_text(s)
