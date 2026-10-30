"""Remove v136's same-inode copy; retain every other payload byte."""
from pathlib import Path
import json
from vendor_ramdisk_edit import edit, sha

r = Path(__file__).resolve().parent.parent
p = 'sheng-compat-v118/'
script_name = p + 'graphics/apply-hardware-v116.sh'
manifest_name = p + 'MANIFEST.json'

def mutate(entries):
    f, old = entries[script_name]
    bad = b'$B cp /compat/bluetooth-v136/ohos/libbt_vendor.z.so $R/compat/bluetooth-v136/ohos/\n'
    assert old.count(bad) == 1
    new = old.replace(bad, b'# /compat is already the RAM root compat alias; do not copy onto itself.\n')
    entries[script_name] = (f.copy(), new)
    mf, mb = entries[manifest_name]
    manifest = json.loads(mb)
    manifest[script_name[len(p):]].update(bytes=len(new), sha256=sha(new))
    entries[manifest_name] = (mf.copy(), (json.dumps(manifest, indent=2)+'\n').encode())

image = edit(r/'output/vendor_boot_hmos_compat_v136.img',
    'd394116dc00a71177dc3f0343b18bc8e14cf691f657485c8cffd5a432ff0cebd',
    r/'work/bluetooth-persistent-v137', mutate, {script_name, manifest_name})
out = r/'output/vendor_boot_hmos_compat_v137.img'
out.write_bytes(image)
v = json.loads((r/'analysis/bluetooth-v136-verification.json').read_text())
v.update(version='v137', status='built_not_flashed', preserved_v136_entries=True,
    changed_entries=[script_name, manifest_name], same_inode_copy_removed=True,
    vendor_boot=dict(file=out.name, bytes=len(image), sha256=sha(image)))
(r/'analysis/bluetooth-v137-verification.json').write_text(json.dumps(v, indent=2)+'\n')
flash = (r/'output/Flash-CompatV136.ps1').read_text(encoding='utf-8-sig')
flash = flash.replace('v136', 'v137').replace('preserved_v135_entries', 'preserved_v136_entries')
(r/'output/Flash-CompatV137.ps1').write_text(flash, encoding='utf-8-sig')
print(json.dumps(v, indent=2))
