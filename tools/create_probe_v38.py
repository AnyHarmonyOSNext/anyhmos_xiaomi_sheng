"""Create v38 from frozen v37; add explicit GPU diagnostics, no autoload."""
from pathlib import Path
import shutil
r=Path(__file__).resolve().parent.parent
for name in ['hmos_probe.c','probe_graphics.inc','probe_command.inc']:shutil.copy2(r/'tools'/name,r/'tools/archive'/(Path(name).stem+'_v37'+Path(name).suffix))
p=r/'tools/hmos_probe.c';s=p.read_text();s=s.replace('v37','v38');p.write_text(s)
p=r/'tools/probe_graphics.inc';s=p.read_text();s=s.replace('"sheng_hdi_smq"','"sheng_hdi_smq","sheng_hdi_scanout","libvulkan_freedreno.so","native_buffer_contract","rosen_gpu_contract"');p.write_text(s)
shutil.copy2(r/'tools/configs/init-core-v37.cfg',r/'tools/configs/init-core-v38.cfg')
dst=r/'compat/sheng-graphics/v38';shutil.copytree(r/'compat/sheng-graphics/v37',dst,dirs_exist_ok=True)
for src in (r/'compat/sheng-graphics/gpu-v1').iterdir():shutil.copy2(src,dst/src.name)
shutil.copy2(r/'compat/sheng-graphics/client-frame-v2/sheng_hdi_scanout',dst/'sheng_hdi_scanout')
s=(r/'tools/build_probe_v37.py').read_text().replace('v37','v38')
s=s.replace('import hashlib','import hashlib\nimport gzip')
s=s.replace("(build / 'ramdisk.cpio').write_bytes(out)","(build / 'ramdisk.raw.cpio').write_bytes(out)\n    # CONFIG_RD_GZIP=y verified in the exact running kernel build.\n    (build / 'ramdisk.cpio').write_bytes(gzip.compress(bytes(out), compresslevel=9, mtime=0))")
s=s.replace("[magisk, 'repack',","[magisk, 'repack', '-n',")
(r/'tools/build_probe_v38.py').write_text(s)
s=(r/'tools/verify_v37.py').read_text().replace('v37','v38')
(r/'tools/verify_v38.py').write_text(s)
