"""Add a private test archive; no global EGL loader or startup changes."""
from pathlib import Path
import json
from vendor_ramdisk_edit import edit, sha
r=Path(__file__).resolve().parent.parent; prefix='sheng-compat-v118/'; manifest={}
added={prefix+'graphics/zink-private-test.tar.gz'}
def mutate(entries):
    data=(r/'compat/sheng-graphics/zink-private-v125/zink-private-test.tar.gz').read_bytes()
    fields=[0,0o100755,0,0,1,0,len(data),0,0,0,0,0,0]
    entries[next(iter(added))]=(fields,data)
    manifest.update({n[len(prefix):]:dict(bytes=len(b),mode=oct(f[1]),sha256=sha(b)) for n,(f,b) in entries.items() if n.startswith(prefix) and n!=prefix+'MANIFEST.json'})
    name=prefix+'MANIFEST.json'; f,_=entries[name]
    entries[name]=(f.copy(),(json.dumps(manifest,indent=2)+'\n').encode())
allowed=added|{prefix+'MANIFEST.json'}
image=edit(r/'output/vendor_boot_hmos_compat_v124.img','7763f5d4ff3d8388659052e7ca99843601461d559e44a65bf064530e7e837507',r/'work/zink-test-v125',mutate,allowed,added)
out=r/'output/vendor_boot_hmos_compat_v125.img'; out.write_bytes(image)
report=dict(version='v125',status='built_not_flashed',vendor_boot=dict(file=out.name,bytes=len(image),sha256=sha(image)),cpio_verified=True,preserved_v124_entries=True,changed_entries=sorted(allowed),init_boot_unchanged=True,dtb_unchanged=True,bootconfig_unchanged=True,stock_vendor_modules_and_audio_unchanged=True,usb_v121_unchanged=True,metadata_v124_unchanged=True,global_egl_unchanged=True,private_zink_test_only=True,cold_boot_verified=False)
(r/'analysis/zink-test-v125-verification.json').write_text(json.dumps(report,indent=2)+'\n')
(r/'output/v125-payload-manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
script=(r/'output/Flash-CompatV124.ps1').read_text(encoding='utf-8-sig').replace('v124','v125').replace('metadata-v125-verification','zink-test-v125-verification').replace('preserved_v123_entries','preserved_v124_entries')
(r/'output/Flash-CompatV125.ps1').write_text(script,encoding='utf-8-sig')
print(json.dumps(report,indent=2))
