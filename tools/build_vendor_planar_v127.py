"""Stage explicit planar YUV allocation/import, retaining the v126 baseline."""
from pathlib import Path
import json
from vendor_ramdisk_edit import edit,sha
r=Path(__file__).resolve().parent.parent;prefix='sheng-compat-v118/';manifest={}
report=json.loads((r/'compat/sheng-graphics/planar-v127/manifest.json').read_text())
def mutate(entries):
 for name,local,expected in [
  ('graphics/libdisplay_buffer_vdi_impl.z.so','libdisplay_buffer_vdi_impl.z.so','47809b4e435697d6ec91365fe8eaeae8e897d347e0958c79149f34fb80475ac8'),
  ('graphics/libvulkan_freedreno.so.gz','libvulkan_freedreno.so.gz',None)]:
  name=prefix+name;f,old=entries[name]
  if expected:assert sha(old)==expected
  new=(r/'compat/sheng-graphics/planar-v127'/local).read_bytes();assert sha(new)==report[local]['sha256']
  entries[name]=(f.copy(),new)
 name=prefix+'graphics/apply-compat-paths.sh';f,old=entries[name]
 oldsha='5064973ec0fc7300fbbab9da5b7b1967fe18f5594315a32a7eac8ce82299be6e';assert old.count(oldsha.encode())==1
 entries[name]=(f.copy(),old.replace(oldsha.encode(),report['libvulkan_freedreno.so']['sha256'].encode()))
 manifest.update({n[len(prefix):]:dict(bytes=len(b),mode=oct(f[1]),sha256=sha(b)) for n,(f,b) in entries.items() if n.startswith(prefix) and n!=prefix+'MANIFEST.json'})
 name=prefix+'MANIFEST.json';f,_=entries[name];entries[name]=(f.copy(),(json.dumps(manifest,indent=2)+'\n').encode())
allowed={prefix+n for n in ['graphics/libdisplay_buffer_vdi_impl.z.so','graphics/libvulkan_freedreno.so.gz','graphics/apply-compat-paths.sh','MANIFEST.json']}
image=edit(r/'output/vendor_boot_hmos_compat_v126.img','89c80804adb94c204b201563983b2f1453c62edb37b00e5fdd1633d12bee8192',r/'work/planar-v127',mutate,allowed)
out=r/'output/vendor_boot_hmos_compat_v127.img';out.write_bytes(image)
verification=dict(version='v127',status='built_not_flashed',vendor_boot=dict(file=out.name,bytes=len(image),sha256=sha(image)),cpio_verified=True,preserved_v126_entries=True,changed_entries=sorted(allowed),init_boot_unchanged=True,dtb_unchanged=True,bootconfig_unchanged=True,stock_vendor_modules_and_audio_unchanged=True,usb_v121_unchanged=True,egl_v126_unchanged=True,original_gpu_governor_unchanged=True,planar_allocator_real_test_passed=True,cold_boot_verified=False,planar_gpu_pixels_verified=False)
(r/'analysis/planar-v127-verification.json').write_text(json.dumps(verification,indent=2)+'\n')
(r/'output/v127-payload-manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
script=(r/'output/Flash-CompatV126.ps1').read_text(encoding='utf-8-sig').replace('v126','v127').replace('egl-v127-verification','planar-v127-verification').replace('preserved_v125_entries','preserved_v126_entries')
(r/'output/Flash-CompatV127.ps1').write_text(script,encoding='utf-8-sig')
print(json.dumps(verification,indent=2))
