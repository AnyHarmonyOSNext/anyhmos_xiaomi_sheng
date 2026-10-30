"""Persist the independently tested RGB metadata allocator, retain v128 GPU."""
from pathlib import Path
import json
from vendor_ramdisk_edit import edit, sha

r = Path(__file__).resolve().parent.parent
prefix = 'sheng-compat-v118/'
manifest = {}
local = r / 'compat/sheng-graphics/rgb-metadata-v129'
report = json.loads((local / 'manifest.json').read_text())

def mutate(entries):
    name = prefix + 'graphics/libdisplay_buffer_vdi_impl.z.so'
    fields, old = entries[name]
    assert sha(old) == '613803a7210a406d822a797f775a5dc017237decca3e71217c0978464511086e'
    new = (local / 'libdisplay_buffer_vdi_impl.z.so').read_bytes()
    assert sha(new) == report['libdisplay_buffer_vdi_impl.z.so']['sha256']
    entries[name] = (fields.copy(), new)
    manifest.update({n[len(prefix):]: dict(bytes=len(blob), mode=oct(f[1]), sha256=sha(blob))
                     for n, (f, blob) in entries.items()
                     if n.startswith(prefix) and n != prefix + 'MANIFEST.json'})
    name = prefix + 'MANIFEST.json'
    fields, _ = entries[name]
    entries[name] = (fields.copy(), (json.dumps(manifest, indent=2) + '\n').encode())

allowed = {prefix + 'graphics/libdisplay_buffer_vdi_impl.z.so', prefix + 'MANIFEST.json'}
image = edit(r / 'output/vendor_boot_hmos_compat_v128.img',
             '471a9463ae5fca7f71415e6c2bdb9f929852d2d162a400421415ecf6d8eb481d',
             r / 'work/rgb-metadata-v129', mutate, allowed)
out = r / 'output/vendor_boot_hmos_compat_v129.img'
out.write_bytes(image)
verification = dict(version='v129', status='built_not_flashed',
    vendor_boot=dict(file=out.name, bytes=len(image), sha256=sha(image)),
    cpio_verified=True, preserved_v128_entries=True,
    changed_entries=sorted(allowed), init_boot_unchanged=True,
    dtb_unchanged=True, bootconfig_unchanged=True,
    stock_vendor_modules_and_audio_unchanged=True, usb_v121_unchanged=True,
    egl_v126_unchanged=True, planar_gpu_v128_unchanged=True,
    original_gpu_governor_unchanged=True, blob_allocation_unchanged=True,
    rgb_yuv_metadata_cross_process_test_passed=True, cold_boot_verified=False,
    contract_proof='output/logs/command-shell-20261030-091948-f3e93395b63d.log')
(r / 'analysis/rgb-metadata-v129-verification.json').write_text(json.dumps(verification, indent=2) + '\n')
(r / 'output/v129-payload-manifest.json').write_text(json.dumps(manifest, indent=2) + '\n')
script = (r / 'output/Flash-CompatV128.ps1').read_text(encoding='utf-8-sig')
script = script.replace('v128', 'v129').replace('planar-view-v129-verification', 'rgb-metadata-v129-verification').replace('preserved_v127_entries', 'preserved_v128_entries')
(r / 'output/Flash-CompatV129.ps1').write_text(script, encoding='utf-8-sig')
print(json.dumps(verification, indent=2))
