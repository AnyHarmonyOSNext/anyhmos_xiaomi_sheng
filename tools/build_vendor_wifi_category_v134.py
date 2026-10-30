"""Stage a narrow original wifi_host ioctl adapter from verified v132."""
from pathlib import Path
import json
import subprocess
from vendor_ramdisk_edit import edit, sha

r = Path(__file__).resolve().parent.parent
prefix = 'sheng-compat-v118/'
outdir = r / 'compat/sheng-wireless/category-v134'
binary = outdir / 'libsheng_wifi_category_v134.so'
assert sha(binary.read_bytes()) == '586ddea072b4585044907f819b7335b032d3761884913f5b64d86a77901004a9'
newname = prefix + 'graphics/' + binary.name
cfgname = prefix + 'graphics/init-wifi-v116.cfg'
applyname = prefix + 'graphics/apply-hardware-v116.sh'
allowed = {newname, cfgname, applyname, prefix + 'MANIFEST.json'}
manifest = {}

def mutate(entries):
    f, blob = entries[cfgname]
    cfg = json.loads(blob)
    host = next(s for s in cfg['services'] if s['name'] == 'wifi_host')
    assert host['uid'] == 'wifi_host' and 'env' not in host
    host['env'] = [{'name': 'LD_PRELOAD', 'value': '/compat/lib64/' + binary.name}]
    data = (json.dumps(cfg, indent=2) + '\n').encode()
    entries[cfgname] = (f.copy(), data)
    (outdir / 'init-wifi-v116.cfg').write_bytes(data)

    f, blob = entries[applyname]
    text = blob.decode()
    assert 'libsheng_wifi_category' not in text
    text += '''
# Only wifi_host receives this adapter; original vendor libraries remain intact.
$B mkdir -p $R/compat/lib64
$B cp /graphics/libsheng_wifi_category_v134.so $R/compat/lib64/libsheng_wifi_category_v134.so
$B chmod 0644 $R/compat/lib64/libsheng_wifi_category_v134.so
: > $R/data/local/tmp/sheng-wifi-category-v134.txt
$B chown 3026:3026 $R/data/local/tmp/sheng-wifi-category-v134.txt
$B chmod 0600 $R/data/local/tmp/sheng-wifi-category-v134.txt
'''
    target = outdir / 'apply-hardware-v116.sh'
    target.write_text(text, encoding='utf-8', newline='\n')
    wslpath = '/mnt/c/' + str(target).replace('\\', '/').split(':/', 1)[1]
    subprocess.run(['wsl.exe', '--', 'bash', '-n', wslpath], check=True, capture_output=True)
    entries[applyname] = (f.copy(), text.encode())

    fields = entries[prefix + 'graphics/native_brightness_launcher'][0].copy()
    fields[0] = max(f[0] for f, b in entries.values()) + 1
    fields[1] = 0o100644
    entries[newname] = (fields, binary.read_bytes())
    manifest.update({n[len(prefix):]: dict(bytes=len(b), mode=oct(f[1]), sha256=sha(b))
                     for n, (f, b) in entries.items()
                     if n.startswith(prefix) and n != prefix + 'MANIFEST.json'})
    name = prefix + 'MANIFEST.json'
    f, _ = entries[name]
    entries[name] = (f.copy(), (json.dumps(manifest, indent=2) + '\n').encode())

image = edit(r / 'output/vendor_boot_hmos_compat_v132.img',
             '42f59b550cca6bda6a2fbdcf260771ff12d07ba4a1384eaee5bd1df62b64342f',
             r / 'work/wifi-category-v134', mutate, allowed, added={newname})
out = r / 'output/vendor_boot_hmos_compat_v134.img'
out.write_bytes(image)
verification = dict(version='v134', status='built_not_flashed',
    vendor_boot=dict(file=out.name, bytes=len(image), sha256=sha(image)),
    cpio_verified=True, preserved_v132_entries=True, changed_entries=sorted(allowed),
    init_boot_unchanged=True, dtb_unchanged=True, bootconfig_unchanged=True,
    stock_vendor_modules_and_audio_unchanged=True, usb_v121_unchanged=True,
    graphics_v130_unchanged=True, battery_v131_unchanged=True, startup_v132_unchanged=True,
    original_gpu_governor_unchanged=True, isolated_original_hal_verified=True,
    isolated_passthrough_and_invalid_pointer_verified=True,
    cold_boot_verified=False, native_uid_wifi_category_verified=False,
    original_framework_connected_category_verified=False, wifi_ui_verified=False,
    actual_wifi7_connection_verified=False, library_sha256=sha(binary.read_bytes()))
(r / 'analysis/wifi-category-v134-verification.json').write_text(json.dumps(verification, indent=2) + '\n', encoding='utf-8')
(r / 'output/v134-payload-manifest.json').write_text(json.dumps(manifest, indent=2) + '\n', encoding='utf-8')
script = (r / 'output/Flash-CompatV132.ps1').read_text(encoding='utf-8-sig')
script = script.replace('v132', 'v134').replace('startup-video-v134-verification', 'wifi-category-v134-verification').replace('preserved_v131_entries', 'preserved_v132_entries')
(r / 'output/Flash-CompatV134.ps1').write_text(script, encoding='utf-8-sig')
buildpath = r / 'analysis/wifi-category-build-v134.json'
build = json.loads(buildpath.read_text(encoding='utf-8'))
build.update(status='isolated_original_hal_verified',
    baseline_log='output/logs/command-shell-20261030-113230-d8407c90101d.log',
    adapted_log='output/logs/command-shell-20261030-113311-1e3eebe3ccff.log',
    production_host_identity_log='output/logs/command-shell-20261030-113350-44f9d37d60d2.log')
buildpath.write_text(json.dumps(build, indent=2) + '\n', encoding='utf-8')
print(json.dumps(verification, indent=2))
