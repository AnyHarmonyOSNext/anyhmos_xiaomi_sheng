"""Persist standard key 12 storage while keeping the v129 graphics baseline."""
from pathlib import Path
import json
from vendor_ramdisk_edit import edit,sha
r=Path(__file__).resolve().parent.parent;prefix='sheng-compat-v118/';manifest={}
local=r/'compat/sheng-graphics/alpha-metadata-v130'
report=json.loads((local/'manifest.json').read_text())
def mutate(entries):
 name=prefix+'graphics/libdisplay_buffer_vdi_impl.z.so';fields,old=entries[name]
 assert sha(old)=='185e8d8e400f14d467c1f742f542225b1ad03dedb603f47f189f32edf6a28e24'
 new=(local/'libdisplay_buffer_vdi_impl.z.so').read_bytes()
 assert sha(new)==report['libdisplay_buffer_vdi_impl.z.so']['sha256']
 entries[name]=(fields.copy(),new)
 manifest.update({n[len(prefix):]:dict(bytes=len(blob),mode=oct(f[1]),sha256=sha(blob))
  for n,(f,blob) in entries.items() if n.startswith(prefix) and n!=prefix+'MANIFEST.json'})
 name=prefix+'MANIFEST.json';fields,_=entries[name]
 entries[name]=(fields.copy(),(json.dumps(manifest,indent=2)+'\n').encode())
allowed={prefix+'graphics/libdisplay_buffer_vdi_impl.z.so',prefix+'MANIFEST.json'}
image=edit(r/'output/vendor_boot_hmos_compat_v129.img',
 '7525ba014f3c297bedc6839c610c499f39c9c80a0cc9a71dbd01d3ed0a4a7ddc',
 r/'work/alpha-metadata-v130',mutate,allowed)
out=r/'output/vendor_boot_hmos_compat_v130.img';out.write_bytes(image)
verification=dict(version='v130',status='built_not_flashed',
 vendor_boot=dict(file=out.name,bytes=len(image),sha256=sha(image)),
 cpio_verified=True,preserved_v129_entries=True,changed_entries=sorted(allowed),
 init_boot_unchanged=True,dtb_unchanged=True,bootconfig_unchanged=True,
 stock_vendor_modules_and_audio_unchanged=True,usb_v121_unchanged=True,
 egl_v126_unchanged=True,planar_gpu_v128_unchanged=True,
 original_gpu_governor_unchanged=True,blob_allocation_unchanged=True,
 metadata_cross_process_test_passed=True,metadata_page_version=3,
 observed_key=12,observed_value=-1,range_checked=[-1,255],
 contract_proof='output/logs/command-shell-20261030-094945-48586afdf38d.log',
 production_probe_proof='output/logs/v129-metadata-values.trace.gz',
 cold_boot_verified=False,hardware_force_alpha_effect_verified=False)
(r/'analysis/alpha-metadata-v130-verification.json').write_text(json.dumps(verification,indent=2)+'\n')
(r/'output/v130-payload-manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
script=(r/'output/Flash-CompatV129.ps1').read_text(encoding='utf-8-sig')
script=script.replace('v129','v130').replace('rgb-metadata-v130-verification','alpha-metadata-v130-verification').replace('preserved_v128_entries','preserved_v129_entries')
(r/'output/Flash-CompatV130.ps1').write_text(script,encoding='utf-8-sig')
print(json.dumps(verification,indent=2))
