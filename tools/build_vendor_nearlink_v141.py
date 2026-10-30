"""Correct donor NearLink capability in the volatile sys_prod overlay before init."""
from pathlib import Path
import json
import subprocess
from vendor_ramdisk_edit import edit, sha

r = Path(__file__).resolve().parent.parent
p = 'sheng-compat-v118/'
apply = p + 'graphics/apply-hardware-v116.sh'
payload = p + 'graphics/hw_defaults-v141.para'
manifest = p + 'MANIFEST.json'
allowed = {apply, payload, manifest}
work = r / 'work/nearlink-persistent-v141'
work.mkdir(exist_ok=True)
original = (r / 'work/donor-capabilities-v141/sys_prod/etc/param/hw_defaults.para').read_bytes()
original_sha = '47e94ce212bf301531e1e0f6480f9b4c566296a557e8fc03b44d958ed81fe8a2'
assert sha(original) == original_sha
assert original.splitlines().count(b'const.nearlink.enable=true') == 1
corrected = original.replace(b'const.nearlink.enable=true', b'const.nearlink.enable=false')
assert corrected.replace(b'const.nearlink.enable=false', b'const.nearlink.enable=true') == original

def mutate(entries):
    f = entries[apply][0].copy()
    f[0] = max(v[0][0] for v in entries.values()) + 1
    f[1] = 0o100644
    entries[payload] = (f, corrected)
    f, b = entries[apply]
    text = b.decode() + f'''
# sheng has no NearLink hardware. Correct only the donor capability in RAM.
capability=$R/sys_prod/etc/param/hw_defaults.para
capability_sha=$($B sha256sum "$capability")
case "$capability_sha" in
 {original_sha}*)
  $B cp /graphics/hw_defaults-v141.para "$capability"
  $B chmod 0644 "$capability"
  ;;
 {sha(corrected)}*) ;;
 *) echo SHENG_V141_CAPABILITY_HASH_MISMATCH >&2; exit 1 ;;
esac
echo SHENG_V141_NEARLINK_UNSUPPORTED_RAM_CAPABILITY
'''
    check = work / 'apply-hardware-v116.sh'
    check.write_text(text, newline='\n')
    wsl = '/mnt/c/' + str(check).replace('\\', '/').split(':/', 1)[1]
    subprocess.run(['wsl.exe', '--', 'bash', '-n', wsl], check=True)
    entries[apply] = (f.copy(), text.encode())
    f, b = entries[manifest]
    m = json.loads(b)
    for n in allowed - {manifest}:
        fs, blob = entries[n]
        m[n[len(p):]] = dict(bytes=len(blob), mode=oct(fs[1]), sha256=sha(blob))
    entries[manifest] = (f.copy(), (json.dumps(m, indent=2) + '\n').encode())

image = edit(r / 'output/vendor_boot_hmos_compat_v140.img',
             '3298a521da701c9ebc95fede8fea5019d6560a7ccbfd38cee4b609accee40215',
             work, mutate, allowed, added={payload})
out = r / 'output/vendor_boot_hmos_compat_v141.img'
out.write_bytes(image)
v = dict(version='v141', status='built_not_flashed', cpio_verified=True,
         vendor_boot=dict(file=out.name, bytes=len(image), sha256=sha(image)),
         preserved_v140_entries=True, changed_entries=sorted(allowed),
         init_boot_unchanged=True, dtb_unchanged=True, bootconfig_unchanged=True,
         stock_vendor_modules_and_audio_unchanged=True, usb_v121_unchanged=True,
         original_gpu_governor_unchanged=True, sys_prod_image_unchanged=True,
         original_parameter_sha256=original_sha, corrected_parameter_sha256=sha(corrected),
         cold_boot_verified=False, normal_reboot_verified=False, bt_ui_three_cycles_verified=False)
(r / 'analysis/nearlink-v141-verification.json').write_text(json.dumps(v, indent=2) + '\n')
flash = (r / 'output/Flash-CompatV140.ps1').read_text(encoding='utf-8-sig')
flash = flash.replace('v140', 'v141').replace('preserved_v139_entries', 'preserved_v140_entries')
flash = flash.replace('softbus-v141-verification', 'nearlink-v141-verification')
(r / 'output/Flash-CompatV141.ps1').write_text(flash, encoding='utf-8-sig')
print(json.dumps(v, indent=2))
