"""Persist the screen-power fix on the verified v143 baseline only."""
from pathlib import Path
import json
from vendor_ramdisk_edit import edit, parse, sha

r = Path(__file__).resolve().parent.parent
prefix = 'sheng-compat-v118/'
work = r/'work/screen-power-persistent-v145'
changes = {
    'graphics/native_display_wake': r/'compat/debug-tools/native_display_wake_v2',
    'graphics/libdisplay_composer_vdi_impl.z.so': r/'compat/sheng-power/screen-v145/libdisplay_composer_vdi_impl.z.so',
}
allowed = {prefix+n for n in changes} | {prefix+'MANIFEST.json'}

def mutate(entries):
    assert sha(entries[prefix+'graphics/native_display_wake'][1]) == \
        'e4f5e084936ed0356a93e97bbaf077f63445b1f8a8ad4dbdf6c0b9480a89dad5'
    assert entries[prefix+'graphics/libdisplay_composer_vdi_impl.z.so'][1] == \
        (r/'compat/sheng-graphics/framepacing-v1/libdisplay_composer_vdi_impl.z.so').read_bytes()
    for n, path in changes.items():
        fields, _ = entries[prefix+n]
        entries[prefix+n] = (fields.copy(), path.read_bytes())
    manifest = {n[len(prefix):]:dict(bytes=len(b),mode=oct(f[1]),sha256=sha(b))
                for n,(f,b) in entries.items()
                if n.startswith(prefix) and n != prefix+'MANIFEST.json'}
    name = prefix+'MANIFEST.json'
    fields, _ = entries[name]
    entries[name] = (fields.copy(),(json.dumps(manifest,indent=2)+'\n').encode())
    for n, info in manifest.items():
        f, b = entries[prefix+n]
        assert info == dict(bytes=len(b),mode=oct(f[1]),sha256=sha(b))

image = edit(r/'output/vendor_boot_hmos_compat_v143.img',
    '74ee88b754f0d62fbd44df964a925d8ca8aaca3592e18ae01aae7ef46ebc4d58',
    work,mutate,allowed)
out = r/'output/vendor_boot_hmos_compat_v145.img'
out.write_bytes(image)
entries = parse((work/'ramdisk.cpio').read_bytes())
# EGL is inside the unchanged graphics payload archive. edit() verifies every
# entry outside the explicit three-entry allowlist byte for byte against v143.
v = dict(version='v145',status='built_not_flashed',cpio_verified=True,
    vendor_boot=dict(file=out.name,bytes=len(image),sha256=sha(image)),
    preserved_v143_entries=True,changed_entries=sorted(allowed),
    compat_manifest_verified=True,init_boot_unchanged=True,dtb_unchanged=True,
    bootconfig_unchanged=True,stock_vendor_modules_and_audio_unchanged=True,
    egl_v143_preserved=True,original_gpu_governor_unchanged=True,
    cold_boot_verified=False,physical_screen_off_verified=False)
(r/'analysis/screen-power-v145-verification.json').write_text(json.dumps(v,indent=2)+'\n')
flash = (r/'output/Flash-CompatV143.ps1').read_text(encoding='utf-8-sig')
flash = flash.replace('v143','v145').replace('V143','V145')
flash = flash.replace('web-bootsound-v145-verification','screen-power-v145-verification')
flash = flash.replace('preserved_v142_entries','preserved_v143_entries')
(r/'output/Flash-CompatV145.ps1').write_text(flash,encoding='utf-8-sig')
print(json.dumps(v,indent=2))
