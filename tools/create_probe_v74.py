"""Freeze v73 and stage verified fence ownership, stock touch and native logs."""
from pathlib import Path
import gzip, json, shutil, subprocess
r = Path(__file__).resolve().parents[1]
for name in ['hmos_probe.c', 'probe_graphics.inc', 'probe_command.inc']:
    p = r / 'tools' / name
    target = r / 'tools/archive' / (p.stem + '_v73' + p.suffix)
    if not target.exists(): shutil.copy2(p, target)
d = r / 'compat/sheng-graphics/v74'
assert not d.exists(), 'Do not rerun staging over reviewed edits'
shutil.copytree(r / 'compat/sheng-graphics/v73', d)
shutil.copy2(r / 'compat/sheng-graphics/fence-v1/libdisplay_composer_vdi_impl.z.so', d)
shutil.copy2(r / 'compat/sheng-touch/v1/touch-bundle.tar.gz', d)
sdk = '/root/hmos-work/sdk-6.0.0.47/installed/native/llvm/bin/'
base = '/mnt/c/SHENG_WORKSPACE/'
for name in ['native_input_dispatch', 'native_render_launcher']:
    out = r / 'compat/debug-tools' / name
    subprocess.run(['wsl', '-d', 'Ubuntu-22.04', '--', sdk + 'clang',
        '--target=aarch64-linux-ohos', '-Os', '-Wall', '-Wextra', '-Werror',
        base + 'tools/' + name + '.c', '-o', base + 'compat/debug-tools/' + name], check=True)
    subprocess.run(['wsl', '-d', 'Ubuntu-22.04', '--', sdk + 'llvm-strip',
        base + 'compat/debug-tools/' + name], check=True)
    shutil.copy2(out, d / name)

manifest = json.loads((r / 'compat/sheng-touch/v1/manifest.json').read_text())
script = ['set -e', 'B=/busybox', 'R=/hmos-root',
    '$B tar -xzf /graphics/touch-bundle.tar.gz -C $R/compat']
for name, info in manifest['artifacts'].items():
    script.append('echo "' + info['sha256'] + '  $R/compat/' + name + '" | $B sha256sum -c -')
script += [
    '$B mkdir -p /compat',
    '$B mount --bind $R/compat /compat',
    '$B insmod /lib/modules/spi-msm-geni.ko',
    '$B insmod $R/compat/modules/xiaomi_touch.ko',
    '$B insmod $R/compat/modules/nt36532_touch.ko',
    'echo SHENG_STOCK_TOUCH_STAGED_AND_LOADED_VENDOR_UNTOUCHED']
(d / 'apply-touch.sh').write_text('\n'.join(script) + '\n', newline='\n')

extra = json.loads((d / 'init-desktop-services.cfg').read_text())
extra['services'].append(dict(name='sheng_input_dispatch',
    path=['/compat/bin/native_input_dispatch'], uid='shell', gid=['shell'],
    apl='system_core', permission=['ohos.permission.INJECT_INPUT_EVENT'],
    disabled=1, once=1, sandbox=0, **{'start-mode':'condition'}))
extra['jobs'].append(dict(name='param:sheng-input-dispatch',
    condition='sheng.debug.input.dispatch=true', cmds=['start sheng_input_dispatch']))
(d / 'init-desktop-services.cfg').write_text(json.dumps(extra, indent=2) + '\n')

p = r / 'tools/probe_graphics.inc'
s = p.read_text()
marker = '    struct {const char *sys,*target;gid_t group;int required;} nodes[]={'
assert s.count(marker) == 1
s = s.replace(marker, '''    if(copy_ram_asset("/graphics/native_input_dispatch","/hmos-root/compat/bin/native_input_dispatch",0755)<0||
       copy_ram_asset("/graphics/native_render_launcher","/hmos-root/compat/bin/native_render_launcher",0755)<0||
       copy_ram_asset("/hmos-root/system/bin/uinput","/hmos-root/compat/bin/uinput-original",0755)<0)return -1;
    const char *render_logs[]={"/hmos-root/data/local/tmp/sheng-render-stderr.txt","/hmos-root/data/local/tmp/sheng-mesa.txt"};
    for(unsigned i=0;i<2;i++)if(textfile(render_logs[i],"")<0||chown(render_logs[i],1003,1003)<0||chmod(render_logs[i],0600)<0)return -1;
    const char *input_log="/hmos-root/data/local/tmp/sheng-input-last.log";
    if(textfile(input_log,"")<0||chown(input_log,2000,2000)<0||chmod(input_log,0600)<0)return -1;
    if(graphics_run_script("/graphics/apply-touch.sh")<0)return -1;
''' + marker)
p.write_text(s)
p = r / 'tools/hmos_probe.c'
p.write_text(p.read_text().replace('v73', 'v74'))
cfg = json.loads((r / 'tools/configs/init-core-v73.cfg').read_text())
next(x for x in cfg['services'] if x['name'] == 'render_service')['path'] = ['/compat/bin/native_render_launcher']
(r / 'tools/configs/init-core-v74.cfg').write_text(json.dumps(cfg, indent=2) + '\n')

s = (r / 'tools/build_probe_v73.py').read_text().replace('v73', 'v74')
start = s.index("    for test in ['token_contract','binder_nested']:")
end = s.index("    entries.append(('busybox'", start)
s = s[:start] + '    # Prior IPC contract binaries remain archived in v73.\n' + s[end:]
s = s.replace("paths += [root / 'compat/sheng-hmos-ipc/tests'/test for test in ['token_contract','binder_nested']]", '')
(r / 'tools/build_probe_v74.py').write_text(s)
s = (r / 'tools/verify_v73.py').read_text().replace('v73', 'v74')
s = s.replace(" for test in ['token_contract','binder_nested']:assert new[test][1]==(root/'compat/sheng-hmos-ipc/tests'/test).read_bytes()", " assert 'token_contract' not in new and 'binder_nested' not in new")
s = s.replace("'sheng_userauth_host'}", "'sheng_userauth_host','sheng_input_dispatch'}")
(r / 'tools/verify_v74.py').write_text(s)
print('v74 staged: exact stock touch bundle, owned acquire fences, native stderr, input dispatcher')
