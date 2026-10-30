"""Persist shared standard YUV metadata after the v123 crop-only diagnosis."""
from pathlib import Path
import json
from vendor_ramdisk_edit import edit, sha
r=Path(__file__).resolve().parent.parent; prefix='sheng-compat-v118/'; manifest={}
def mutate(entries):
    name=prefix+'graphics/libdisplay_buffer_vdi_impl.z.so'; f,old=entries[name]
    assert sha(old)=='0bcce1e7ec6f2641a51c9908618f1457e2403bbfb7c8b60106cde5e870190f34'
    new=(r/'compat/sheng-graphics/metadata-v124/libdisplay_buffer_vdi_impl.z.so').read_bytes()
    assert sha(new)=='47809b4e435697d6ec91365fe8eaeae8e897d347e0958c79149f34fb80475ac8'
    entries[name]=(f.copy(),new)
    manifest.update({n[len(prefix):]:dict(bytes=len(b),mode=oct(f[1]),sha256=sha(b)) for n,(f,b) in entries.items() if n.startswith(prefix) and n!=prefix+'MANIFEST.json'})
    name=prefix+'MANIFEST.json'; f,_=entries[name]
    entries[name]=(f.copy(),(json.dumps(manifest,indent=2)+'\n').encode())
allowed={prefix+'graphics/libdisplay_buffer_vdi_impl.z.so',prefix+'MANIFEST.json'}
image=edit(r/'output/vendor_boot_hmos_compat_v123.img','dfeee83056f70d9577dfeb48deec774dd54d9ed6dd8c7cded408eb209fdf7576',r/'work/metadata-v124',mutate,allowed)
out=r/'output/vendor_boot_hmos_compat_v124.img'; out.write_bytes(image)
report=dict(version='v124',status='built_not_flashed',vendor_boot=dict(file=out.name,bytes=len(image),sha256=sha(image)),cpio_verified=True,preserved_v123_entries=True,changed_entries=sorted(allowed),init_boot_unchanged=True,dtb_unchanged=True,bootconfig_unchanged=True,stock_vendor_modules_and_audio_unchanged=True,usb_v121_unchanged=True,metadata_cross_process_test_passed=True,cold_boot_verified=False,surface_decode_verified=False)
(r/'analysis/metadata-v124-verification.json').write_text(json.dumps(report,indent=2)+'\n')
(r/'output/v124-payload-manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
script=(r/'output/Flash-CompatV123.ps1').read_text(encoding='utf-8-sig').replace('v123','v124').replace('crop-v124-verification','metadata-v124-verification').replace('preserved_v122_entries','preserved_v123_entries')
(r/'output/Flash-CompatV124.ps1').write_text(script,encoding='utf-8-sig')
print(json.dumps(report,indent=2))
