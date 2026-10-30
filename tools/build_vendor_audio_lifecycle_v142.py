"""Persist the tested PAL standby lifecycle fix; retain every unrelated entry."""
from pathlib import Path
import json
from vendor_ramdisk_edit import edit, parse, sha

r = Path(__file__).resolve().parent.parent
work = r / 'work/audio-lifecycle-persistent-v142'
work.mkdir(exist_ok=True)
prefix = 'sheng-audio-v1/'
library = 'audio/native/lib64/libsheng_audio_vdi.so'
allowed = {prefix + library, prefix + 'SHA256SUMS', prefix + 'manifest.json'}
old_sha = '800806ca2fc2fc2c85116310a4c127603f4dd860ad018513be933b65929d1ecd'
new_sha = 'bdb31b5b56c379ca1141bc9bfa0d9067c45ebb2df47b4b664a83fed7964248ca'
payload = (r / 'compat/sheng-audio/lifecycle-v142/libsheng_audio_vdi.so').read_bytes()
assert sha(payload) == new_sha and len(payload) == 22120


def mutate(entries):
    fields, old = entries[prefix + library]
    assert sha(old) == old_sha
    entries[prefix + library] = (fields.copy(), payload)
    fields, checksums = entries[prefix + 'SHA256SUMS']
    assert checksums.count(old_sha.encode()) == 1
    checksums = checksums.replace(old_sha.encode(), new_sha.encode())
    entries[prefix + 'SHA256SUMS'] = (fields.copy(), checksums)
    fields, raw = entries[prefix + 'manifest.json']
    m = json.loads(raw)
    assert m['files'][library] == dict(bytes=len(old), sha256=old_sha)
    m['files'][library] = dict(bytes=len(payload), sha256=new_sha)
    entries[prefix + 'manifest.json'] = (fields.copy(), (json.dumps(m, indent=2) + '\n').encode())
    # This separate original audio payload is outside the compat manifest scope.
    global_manifest = json.loads(entries['sheng-compat-v118/MANIFEST.json'][1])
    assert not any(name.startswith(prefix) for name in global_manifest)
    for line in checksums.decode().splitlines():
        digest, name = line.split('  ', 1)
        assert sha(entries[prefix + name][1]) == digest, name
    for name, item in m['files'].items():
        blob = entries[prefix + name][1]
        assert len(blob) == item['bytes'] and sha(blob) == item['sha256'], name


image = edit(r / 'output/vendor_boot_hmos_compat_v141.img',
             'f672adb5f6b0d064984fa76310383003e5cebc1461c9e49b10a48a7d43ea52d0',
             work, mutate, allowed)
out = r / 'output/vendor_boot_hmos_compat_v142.img'
out.write_bytes(image)
assert parse((work / 'ramdisk.cpio').read_bytes())[prefix + library][1] == payload
v = dict(version='v142', status='built_not_flashed', cpio_verified=True,
         vendor_boot=dict(file=out.name, bytes=len(image), sha256=sha(image)),
         preserved_v141_entries=True, changed_entries=sorted(allowed),
         audio_payload_checksums_verified=True, audio_library_sha256=new_sha,
         hot_playback_user_confirmed=True, hot_pause_resume_user_confirmed=True,
         cold_boot_verified=False, normal_reboot_verified=False,
         init_boot_unchanged=True, dtb_unchanged=True, bootconfig_unchanged=True,
         stock_vendor_modules_unchanged=True, usb_v121_unchanged=True,
         original_gpu_governor_unchanged=True,
         hardware_volume_unchanged=True,
         usb_first_boot_role_drop_fixed=False)
(r / 'analysis/audio-lifecycle-v142-verification.json').write_text(json.dumps(v, indent=2) + '\n')
flash = (r / 'output/Flash-CompatV141.ps1').read_text(encoding='utf-8-sig')
flash = flash.replace('v141', 'v142').replace('V141', 'V142')
flash = flash.replace('preserved_v140_entries', 'preserved_v141_entries')
flash = flash.replace('nearlink-v142-verification', 'audio-lifecycle-v142-verification')
flash = flash.replace('$v.stock_vendor_modules_and_audio_unchanged',
                      '$v.stock_vendor_modules_unchanged -or -not $v.audio_payload_checksums_verified')
(r / 'output/Flash-CompatV142.ps1').write_text(flash, encoding='utf-8-sig')
print(json.dumps(v, indent=2))
