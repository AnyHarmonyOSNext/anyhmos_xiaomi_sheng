from pathlib import Path
import json
from vendor_ramdisk_edit import edit,sha
r=Path(__file__).resolve().parent.parent;prefix='sheng-compat-v118/';manifest={}
report=json.loads((r/'compat/sheng-graphics/planar-view-v128/manifest.json').read_text())
def mutate(entries):
 name=prefix+'graphics/libvulkan_freedreno.so.gz';f,old=entries[name]
 assert sha(old)=='335ee2544add80fe478f52cadef544417e8cd3ead5662e348f6bf59c446685c2'
 new=(r/'compat/sheng-graphics/planar-view-v128/libvulkan_freedreno.so.gz').read_bytes();assert sha(new)==report['libvulkan_freedreno.so.gz']['sha256'];entries[name]=(f.copy(),new)
 name=prefix+'graphics/apply-compat-paths.sh';f,old=entries[name]
 oldsha='48a2ca02cb20f19ef15184b5923a5133c8f690e0b94c5bd460fd48fcbfa00b2b';assert old.count(oldsha.encode())==1
 entries[name]=(f.copy(),old.replace(oldsha.encode(),report['libvulkan_freedreno.so']['sha256'].encode()))
 manifest.update({n[len(prefix):]:dict(bytes=len(b),mode=oct(f[1]),sha256=sha(b)) for n,(f,b) in entries.items() if n.startswith(prefix) and n!=prefix+'MANIFEST.json'})
 name=prefix+'MANIFEST.json';f,_=entries[name];entries[name]=(f.copy(),(json.dumps(manifest,indent=2)+'\n').encode())
allowed={prefix+n for n in ['graphics/libvulkan_freedreno.so.gz','graphics/apply-compat-paths.sh','MANIFEST.json']}
image=edit(r/'output/vendor_boot_hmos_compat_v127.img','bfb4b38dc3b042f90db284a040a245f5a06a1a70daa6505121490708e2646407',r/'work/planar-view-v128',mutate,allowed)
out=r/'output/vendor_boot_hmos_compat_v128.img';out.write_bytes(image)
verification=dict(version='v128',status='built_not_flashed',vendor_boot=dict(file=out.name,bytes=len(image),sha256=sha(image)),cpio_verified=True,preserved_v127_entries=True,changed_entries=sorted(allowed),init_boot_unchanged=True,dtb_unchanged=True,bootconfig_unchanged=True,stock_vendor_modules_and_audio_unchanged=True,usb_v121_unchanged=True,egl_v126_unchanged=True,planar_allocator_v127_unchanged=True,original_gpu_governor_unchanged=True,cold_boot_verified=False,planar_gpu_pixels_verified=False)
(r/'analysis/planar-view-v128-verification.json').write_text(json.dumps(verification,indent=2)+'\n')
(r/'output/v128-payload-manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
script=(r/'output/Flash-CompatV127.ps1').read_text(encoding='utf-8-sig').replace('v127','v128').replace('planar-v128-verification','planar-view-v128-verification').replace('preserved_v126_entries','preserved_v127_entries')
(r/'output/Flash-CompatV128.ps1').write_text(script,encoding='utf-8-sig');print(json.dumps(verification,indent=2))
