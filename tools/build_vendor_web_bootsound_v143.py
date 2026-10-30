"""Persist two tested compatibility fixes without changing donor partitions."""
from pathlib import Path
import gzip
import json
import subprocess
from vendor_ramdisk_edit import edit, parse, sha

r = Path(__file__).resolve().parent.parent
prefix = 'sheng-compat-v118/'
work = r / 'work/web-bootsound-persistent-v143'
dest = r / 'compat/sheng-framework/web-namespace-v143'
old_sha = 'e51c63b4e099a2f927d17f70d037e2687aeff63f84aad2af74a63c4c923329b0'
new_sha = 'efaa00c5e6cda288f33b698920b3e988247e66fcec6b5abad539cc4e51945e5a'
payload = (dest / 'appdata-sandbox.json').read_bytes()
assert sha(payload) == new_sha

allowed = {prefix + 'graphics/appdata-sandbox.json.gz',
           prefix + 'graphics/apply-app-sandbox.sh',
           prefix + 'graphics/start-native-desktop-v116.sh',
           prefix + 'MANIFEST.json'}


def mutate(entries):
    name = prefix + 'graphics/appdata-sandbox.json.gz'
    fields, old = entries[name]
    original = gzip.decompress(old)
    assert sha(original) == old_sha
    before, after = json.loads(original), json.loads(payload)
    expected = json.loads(original)
    for key in ['__internal__.com.ohos.render', '__internal__.com.ohos.gpu']:
        matches = [item[key] for item in expected['individual'] if key in item]
        assert len(matches) == 1
        nodes = matches[0]
        # Retain network namespaces, all access rules and mounts.
        assert nodes[0]['sandbox-ns-flags'] == ['pid', 'net']
        nodes[0]['sandbox-ns-flags'] = ['net']
    assert after == expected and after != before
    entries[name] = (fields.copy(), gzip.compress(payload, mtime=0))
    name = prefix + 'graphics/apply-app-sandbox.sh'
    fields, script = entries[name]
    assert script.count(old_sha.encode()) == 1
    entries[name] = (fields.copy(), script.replace(old_sha.encode(), new_sha.encode()))
    name = prefix + 'graphics/start-native-desktop-v116.sh'
    fields, script = entries[name]
    marker = b'stage=bootanimation\ntrace_stage\n'
    assert script.count(marker) == 1
    fallback = b'''# Donor IsNormalBoot explicitly supports UNKNOWN. A missing imported reason
# otherwise makes its original player force volume zero. Preserve every real
# reason and the original persistent sound preference / volume policy.
boot_reason=$($B chroot "$R" /system/bin/param get ohos.boot.reboot_reason 2>/dev/null || :)
case "$boot_reason" in
 ""|"Get parameter "*)
  $B chroot "$R" /system/bin/param set ohos.boot.reboot_reason UNKNOWN
  echo AUTOSTART_BOOT_REASON_MISSING_FALLBACK=UNKNOWN
  ;;
esac
'''
    script = script.replace(marker, marker + fallback)
    target = dest / 'start-native-desktop-v116.sh'
    target.write_bytes(script)
    subprocess.run(['wsl.exe', '--', 'bash', '-n',
                    '/mnt/c/' + str(target).replace('\\', '/').split(':/', 1)[1]],
                   check=True, capture_output=True)
    entries[name] = (fields.copy(), script)
    manifest = {n[len(prefix):]: dict(bytes=len(b), mode=oct(f[1]), sha256=sha(b))
                for n, (f, b) in entries.items()
                if n.startswith(prefix) and n != prefix + 'MANIFEST.json'}
    name = prefix + 'MANIFEST.json'
    fields, _ = entries[name]
    entries[name] = (fields.copy(), (json.dumps(manifest, indent=2) + '\n').encode())
    for name, info in manifest.items():
        fields, blob = entries[prefix + name]
        assert info == dict(bytes=len(blob), mode=oct(fields[1]), sha256=sha(blob))


image = edit(r / 'output/vendor_boot_hmos_compat_v142.img',
             '365a51bb2819e85cb8d4985e1277194640d60b4a7a98db8719611342ba8cf210',
             work, mutate, allowed)
out = r / 'output/vendor_boot_hmos_compat_v143.img'
out.write_bytes(image)
entries = parse((work / 'ramdisk.cpio').read_bytes())
assert sha(entries['sheng-audio-v1/audio/native/lib64/libsheng_audio_vdi.so'][1]) == \
    'bdb31b5b56c379ca1141bc9bfa0d9067c45ebb2df47b4b664a83fed7964248ca'
v = dict(version='v143', status='built_not_flashed', cpio_verified=True,
         vendor_boot=dict(file=out.name, bytes=len(image), sha256=sha(image)),
         preserved_v142_entries=True, changed_entries=sorted(allowed),
         compat_manifest_verified=True, sandbox_json_sha256=new_sha,
         sandbox_diff_only_render_gpu_pid_namespace=True,
         boot_sound_missing_reason_fallback='UNKNOWN',
         hot_boot_sound_user_confirmed=True, hot_renderer_creation_verified=True,
         webview_content_verified=False, cold_boot_verified=False,
         boot_sound_cold_boot_user_confirmed=False,
         init_boot_unchanged=True, dtb_unchanged=True, bootconfig_unchanged=True,
         stock_vendor_modules_and_audio_unchanged=True,
         original_gpu_governor_unchanged=True, usb_v121_unchanged=True)
(r / 'analysis/web-bootsound-v143-verification.json').write_text(json.dumps(v, indent=2) + '\n')
flash = (r / 'output/Flash-CompatV142.ps1').read_text(encoding='utf-8-sig')
flash = flash.replace('v142', 'v143').replace('V142', 'V143')
flash = flash.replace('preserved_v141_entries', 'preserved_v142_entries')
flash = flash.replace('audio-lifecycle-v143-verification', 'web-bootsound-v143-verification')
flash = flash.replace('$v.stock_vendor_modules_unchanged -or -not $v.audio_payload_checksums_verified',
                      '$v.stock_vendor_modules_and_audio_unchanged -or -not $v.compat_manifest_verified')
(r / 'output/Flash-CompatV143.ps1').write_text(flash, encoding='utf-8-sig')
print(json.dumps(v, indent=2))
