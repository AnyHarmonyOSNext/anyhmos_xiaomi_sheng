"""Start the donor SoftBus under its real identity after the working BT port."""
from pathlib import Path
import copy
import json
import subprocess
from vendor_ramdisk_edit import edit, sha

r = Path(__file__).resolve().parent.parent
p = 'sheng-compat-v118/'
base = r / 'work/hmos_system/system/system'
cfg = p + 'bluetooth-v136/init-bluetooth-v136.cfg'
profile = p + 'bluetooth-v136/softbus_server.json'
apply = p + 'graphics/apply-hardware-v116.sh'
checks = p + 'bluetooth-v136/SHA256SUMS'
manifest = p + 'MANIFEST.json'
allowed = {cfg, profile, apply, checks, manifest}
original = json.loads((base / 'etc/init/softbus_server_musl.cfg').read_text())
svc = copy.deepcopy(original['services'][0])
assert svc['name'] == 'softbus_server' and svc['uid'] == 'dsoftbus'
# Never promote a new peripheral dependency to a reboot-critical service.
svc.pop('critical', None)
svc.update(disabled=1, once=1, sandbox=0, saspawn=False, **{'start-mode': 'condition'})
assert svc['permission'] == original['services'][0]['permission']
assert svc['permission_acls'] == original['services'][0]['permission_acls']
raw_profile = (base / 'profile/softbus_server.json').read_bytes()
assert json.loads(raw_profile)['systemability'][0]['name'] == 4700


def mutate(entries):
    f = entries[p + 'bluetooth-v136/bluetooth_service_v136.json'][0].copy()
    f[0] = max(fs[0] for fs, b in entries.values()) + 1
    entries[profile] = (f, raw_profile)
    f, b = entries[cfg]
    c = json.loads(b)
    assert not any(s['name'] == svc['name'] for s in c['services'])
    c['services'].append(svc)
    job = next(j for j in c['jobs'] if j['name'] == 'param:sheng-bluetooth-v136')
    # Keep the shared database parent permissions unchanged.
    job['cmds'] += [
        'mkdir /data/service/el1/public/dsoftbus 0771 dsoftbus dsoftbus',
        'mkdir /data/service/el1/public/database/dsoftbus 02770 dsoftbus ddms',
        'start softbus_server',
    ]
    entries[cfg] = (f.copy(), (json.dumps(c, indent=2) + '\n').encode())
    f, b = entries[apply]
    text = b.decode() + '\n# Original SoftBus profile in the RAM system overlay.\n'
    text += '$B cp /compat/bluetooth-v136/softbus_server.json $R/system/profile/softbus_server.json\n'
    check_path = r / 'work/bluetooth-persistent-v140/apply-hardware-v116.sh'
    check_path.write_text(text, newline='\n')
    wsl = '/mnt/c/' + str(check_path).replace('\\', '/').split(':/', 1)[1]
    subprocess.run(['wsl.exe', '--', 'bash', '-n', wsl], check=True)
    entries[apply] = (f.copy(), text.encode())
    f, _ = entries[checks]
    names = sorted(n for n in entries if n.startswith(p + 'bluetooth-v136/')
                   and n != checks and (entries[n][0][1] & 0o170000) == 0o100000)
    entries[checks] = (f.copy(), ''.join(sha(entries[n][1]) + '  ' + n[len(p + 'bluetooth-v136/'):]
                                      + '\n' for n in names).encode())
    f, b = entries[manifest]
    m = json.loads(b)
    for n in allowed - {manifest}:
        fs, blob = entries[n]
        m[n[len(p):]] = dict(bytes=len(blob), mode=oct(fs[1]), sha256=sha(blob))
    entries[manifest] = (f.copy(), (json.dumps(m, indent=2) + '\n').encode())


image = edit(r / 'output/vendor_boot_hmos_compat_v139.img',
             'ab315aa17215b734041dc1c81b8c8abd50a4b284d786e09b469e85dce4a0cadb',
             r / 'work/bluetooth-persistent-v140', mutate, allowed, added={profile})
out = r / 'output/vendor_boot_hmos_compat_v140.img'
out.write_bytes(image)
v = dict(version='v140', status='built_not_flashed', cpio_verified=True,
         vendor_boot=dict(file=out.name, bytes=len(image), sha256=sha(image)),
         preserved_v139_entries=True, changed_entries=sorted(allowed),
         init_boot_unchanged=True, dtb_unchanged=True, bootconfig_unchanged=True,
         stock_vendor_modules_and_audio_unchanged=True, usb_v121_unchanged=True,
         wifi_v134_unchanged=True, original_gpu_governor_unchanged=True,
         original_softbus_profile_sha256=sha(raw_profile),
         original_softbus_permissions_preserved=True, critical_restart_disabled=True,
         dm_source_reference_commit='2adef0db2499308206951284bfa49bee675ea0d6',
         cold_boot_verified=False, normal_reboot_verified=False,
         softbus_sa_verified=False, device_manager_sa_verified=False)
(r / 'analysis/softbus-v140-verification.json').write_text(json.dumps(v, indent=2) + '\n')
flash = (r / 'output/Flash-CompatV139.ps1').read_text(encoding='utf-8-sig')
flash = flash.replace('v139', 'v140').replace('preserved_v138_entries', 'preserved_v139_entries')
flash = flash.replace('bluetooth-v140-verification', 'softbus-v140-verification')
(r / 'output/Flash-CompatV140.ps1').write_text(flash, encoding='utf-8-sig')
print(json.dumps(v, indent=2))
