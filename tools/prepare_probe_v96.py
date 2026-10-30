"""Give the bounded preload client a normal init-created BMS permission token."""
from pathlib import Path
import json
import shutil
import subprocess

r = Path(__file__).resolve().parent.parent
d = r / 'compat/sheng-graphics/v96'
assert not d.exists()
shutil.copytree(r / 'compat/sheng-graphics/v95', d)
for p in list(d.iterdir()):
    if p.is_file() and p.suffix in {'.sh', '.cfg'}:
        q = p.with_name(p.name.replace('v95', 'v96'))
        s = p.read_text(encoding='utf-8').replace('v95', 'v96').replace('V95', 'V96')
        if q != p:
            p.unlink()
        q.write_text(s, encoding='utf-8', newline='\n')
for name in ['hmos_probe_v95.c', 'probe_graphics_v95.inc', 'probe_command_v95.inc',
             'build_probe_v95.py', 'verify_v95.py', 'start_native_desktop_v95.sh']:
    (r / 'tools' / name.replace('v95', 'v96')).write_text(
        (r / 'tools' / name).read_text(encoding='utf-8').replace('v95', 'v96'),
        encoding='utf-8', newline='\n')
(r / 'tools/configs/init-core-v96.cfg').write_text(
    (r / 'tools/configs/init-core-v95.cfg').read_text(encoding='utf-8').replace('v95', 'v96'),
    encoding='utf-8', newline='\n')
sdk = '/root/hmos-work/sdk-6.0.0.47/installed/native/llvm/bin/'
base = '/mnt/c/SHENG_WORKSPACE/'
subprocess.run(['wsl', '-d', 'Ubuntu-22.04', '--', sdk + 'clang',
    '--target=aarch64-linux-ohos', '-Os', '-Wall', '-Wextra', '-Werror',
    base + 'tools/native_bundle_cli.c', '-o', base + 'compat/debug-tools/native_bundle_cli'], check=True)
subprocess.run(['wsl', '-d', 'Ubuntu-22.04', '--', sdk + 'llvm-strip',
    base + 'compat/debug-tools/native_bundle_cli'], check=True)
shutil.copyfile(r / 'compat/debug-tools/native_bundle_cli', d / 'native_bundle_cli')
p = d / 'init-desktop-services.cfg'
cfg = json.loads(p.read_text())
permissions = ['ohos.permission.INSTALL_BUNDLE', 'ohos.permission.GET_BUNDLE_INFO_PRIVILEGED',
               'ohos.permission.GET_INSTALLED_BUNDLE_LIST']
cfg['services'].append(dict(name='sheng_bundle_cli', path=['/compat/bin/native_bundle_cli'],
    uid='shell', gid=['shell'], apl='system_core', permission=permissions, permission_acls=permissions,
    disabled=1, once=1, sandbox=0, saspawn=False, **{'start-mode': 'condition'}))
cfg['jobs'].append(dict(name='param:sheng-bundle-cli', condition='sheng.debug.bundle.cli=true', cmds=[
    'write /data/local/tmp/sheng-bundle-last.log ""',
    'chown shell shell /data/local/tmp/sheng-bundle-last.log',
    'chmod 0600 /data/local/tmp/sheng-bundle-last.log', 'start sheng_bundle_cli']))
p.write_text(json.dumps(cfg, indent=2), encoding='utf-8', newline='\n')
p = d / 'apply-preload.sh'
p.write_text(p.read_text() + '''\n$B cp /graphics/native_bundle_cli "$R/compat/bin/native_bundle_cli"
$B chmod 0755 "$R/compat/bin/native_bundle_cli"
''', encoding='utf-8', newline='\n')
p = r / 'tools/verify_v96.py'
s = p.read_text().replace("'sheng_screen_unlock'}", "'sheng_screen_unlock','sheng_bundle_cli'}")
s = s.replace("assert b'apply-preload.sh' in binary", """assert new['graphics/native_bundle_cli'][1]==(root/'compat/debug-tools/native_bundle_cli').read_bytes()
 assert next(x for x in extra['services'] if x['name']=='sheng_bundle_cli')['permission_acls']==['ohos.permission.INSTALL_BUNDLE','ohos.permission.GET_BUNDLE_INFO_PRIVILEGED','ohos.permission.GET_INSTALLED_BUNDLE_LIST']
 assert b'apply-preload.sh' in binary""")
p.write_text(s, encoding='utf-8', newline='\n')
print('v96 staged: one-shot native BMS CLI; never auto-installs or clears userdata')
