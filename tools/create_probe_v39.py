"""Keep original LZ4 ramdisk container; carry GPU as gzip data only."""
from pathlib import Path
import shutil,gzip
r=Path(__file__).resolve().parent.parent
for name in ['hmos_probe.c','probe_graphics.inc','probe_command.inc']:shutil.copy2(r/'tools'/name,r/'tools/archive'/(Path(name).stem+'_v38'+Path(name).suffix))
p=r/'tools/hmos_probe.c';p.write_text(p.read_text().replace('v38','v39'))
p=r/'tools/probe_graphics.inc';p.write_text(p.read_text().replace('"libvulkan_freedreno.so"','"libvulkan_freedreno.so.gz"'))
shutil.copy2(r/'tools/configs/init-core-v38.cfg',r/'tools/configs/init-core-v39.cfg')
dst=r/'compat/sheng-graphics/v39';shutil.copytree(r/'compat/sheng-graphics/v37',dst,dirs_exist_ok=True)
for name in ['native_buffer_contract','rosen_gpu_contract']:shutil.copy2(r/'compat/sheng-graphics/gpu-v1'/name,dst/name)
(dst/'libvulkan_freedreno.so.gz').write_bytes(gzip.compress((r/'compat/sheng-graphics/gpu-v1/libvulkan_freedreno.so').read_bytes(),compresslevel=9,mtime=0))
shutil.copy2(r/'compat/sheng-graphics/client-frame-v2/sheng_hdi_scanout',dst/'sheng_hdi_scanout')
(r/'tools/build_probe_v39.py').write_text((r/'tools/build_probe_v37.py').read_text().replace('v37','v39'))
(r/'tools/verify_v39.py').write_text((r/'tools/verify_v37.py').read_text().replace('v37','v39'))
