"""Prepare vendor-read-only compatibility layer; never edit donor/vendor inputs."""
from pathlib import Path
import base64, hashlib, json, re, shutil, subprocess

r = Path(__file__).resolve().parent.parent
sha = lambda b: hashlib.sha256(b).hexdigest()
archive = r/'tools/archive'
for name in ['hmos_probe.c', 'probe_graphics.inc', 'probe_command.inc']:
    frozen = archive/(Path(name).stem+'_v45'+Path(name).suffix)
    if not frozen.exists(): shutil.copy2(r/'tools'/name, frozen)
dest = r/'compat/sheng-graphics/v46'
shutil.copytree(r/'compat/sheng-graphics/v45', dest, dirs_exist_ok=True)

patches = []
def runtime_patch(name, source, expected, old, new, target, mode):
    raw = source.read_bytes()
    assert sha(raw) == expected, name
    assert raw.count(old) == 1 and len(new) <= len(old), name
    offset = raw.index(old)
    after = new.ljust(len(old), b'\0')
    result = raw[:offset]+after+raw[offset+len(old):]
    spec = {'name': name, 'input_sha256': sha(raw), 'output_sha256': sha(result),
            'source': str(source.relative_to(r)), 'target': target,
            'changes': [{'offset': offset, 'before': old.hex(), 'after': after.hex()}],
            'validation': 'OFFLINE_CANDIDATE_NOT_FLASHED'}
    (dest/(name+'.json')).write_text(json.dumps(spec, indent=2)+'\n')
    # Generated runtime script uses whole-file guards before and after a bounded edit.
    lines = [f'p={target}', f'h=$(/busybox sha256sum {source_paths[name]})',
             f'case "$h" in {sha(raw)}\\ *) ;; *) echo {name}_INPUT_MISMATCH; exit 41;; esac',
             f'/busybox cp {source_paths[name]} "$p.new"',
             f'echo {base64.b64encode(after).decode()} | /busybox base64 -d | /busybox dd of="$p.new" bs=1 seek={offset} conv=notrunc',
             'h=$(/busybox sha256sum "$p.new")',
             f'case "$h" in {sha(result)}\\ *) ;; *) echo {name}_OUTPUT_MISMATCH; exit 42;; esac',
             f'/busybox chmod {mode} "$p.new"', '/busybox mv "$p.new" "$p"']
    patches.extend(lines)
    return spec

source_paths = {'init-compat-scan': '/hmos-root/system/bin/init',
                'vulkan-compat-search': '/hmos-root/system/lib64/libvulkan.so'}
specs = [runtime_patch('init-compat-scan', r/'work/hmos_system/system/system/bin/init',
    'a2d9c09eb841675c39086d7fb6f8769cc9be13099c50c4ed6e05eb1f59c03372',
    b'etc/init\0', b'etc/shng\0', '/hmos-root/compat/bin/init', '755'),
    runtime_patch('vulkan-compat-search', r/'work/donor-hdi-link/libvulkan.so',
    '3d6aa4145996faf241c5e5a2ba1a9161fffe30101c9f19b5f40da25743a5da2d',
    b'/system/etc:/vendor/etc\0', b'/compat/etc\0', '/hmos-root/compat/lib64/libvulkan.so', '644')]
(dest/'apply-compat-paths.sh').write_bytes(('\n'.join(['#!/bin/sh', 'set -e',
    '/busybox mkdir -p /hmos-root/compat/bin /hmos-root/compat/lib64']+patches+
    ['/busybox gzip -dc /graphics/libvulkan_freedreno.so.gz > /hmos-root/compat/lib64/libvulkan_freedreno.so',
     'h=$(/busybox sha256sum /hmos-root/compat/lib64/libvulkan_freedreno.so)',
     'case "$h" in ce6413a25a0fb8cf3cf3d58a0026e506889ab171435b34eb2bc383e6d29503d9\\ *) ;; *) echo GPU_INPUT_MISMATCH; exit 43;; esac',
     '/busybox chmod 644 /hmos-root/compat/lib64/libvulkan_freedreno.so',
     'echo COMPAT_LOADER_PATHS_INSTALLED'])+'\n').encode())

# Preserve namespace inheritance/allowlists; add only the compatibility search directory.
namespace_inputs = []
etc = r/'work/hmos_system/system/system/etc'
for src in sorted(etc.glob('ld-musl-namespace-aarch64*.ini')):
    text = src.read_text(encoding='utf-8')
    text = re.sub(r'(?m)^(\s*systemscence\s*=\s*)', r'\g<1>/compat/bin:', text)
    text, count = re.subn(r'(?m)^(\s*namespace\.[\w.]+\.lib\.paths\s*=\s*)',
                         r'\g<1>/compat/lib64:', text)
    assert count, src
    (dest/src.name).write_text(text, encoding='utf-8')
    namespace_inputs.append({'name': src.name, 'input_sha256': sha(src.read_bytes()), 'path_entries': count})
src = etc/'ld-musl-aarch64.path'
(dest/src.name).write_text('/compat/lib64:'+src.read_text(encoding='utf-8'), encoding='utf-8')
icd = json.loads((dest/'sheng-turnip.json').read_text())
icd['ICD']['library_path'] = '/compat/lib64/libvulkan_freedreno.so'
(dest/'sheng-turnip.json').write_text(json.dumps(icd, indent=2)+'\n')

# Keep the original init service identity/token, but execute the layer's launcher.
launcher = (r/'tools/bootanimation_native_launcher.c').read_text()
launcher = launcher.replace('/data/local/tmp/sheng-graphics/libsheng_boot_vulkan.so', '/compat/lib64/libsheng_boot_vulkan.so')
launcher = launcher.replace('/data/local/tmp/sheng-graphics/bootanimation-real', '/compat/bin/bootanimation-real')
(r/'tools/bootanimation_native_launcher_compat.c').write_text(launcher)
wsl_root = '/mnt/c/'+r.as_posix()[3:]
subprocess.run(['wsl','-d','Ubuntu-22.04','--',
    '/root/hmos-work/sdk-6.0.0.47/installed/native/llvm/bin/clang',
    '--target=aarch64-linux-ohos','-O2',wsl_root+'/tools/bootanimation_native_launcher_compat.c',
    '-o',wsl_root+'/compat/sheng-graphics/v46/bootanimation-launcher'], check=True)

# Existing accepted Rosen fix is produced in the compatibility layer instead of system.
script = (r/'compat/sheng-graphics/v45/apply-rosen-handle.sh').read_text()
script = script.replace('p=/hmos-root/system/lib64/librender_service_base.z.so',
    'source=/hmos-root/system/lib64/librender_service_base.z.so\np=/hmos-root/compat/lib64/librender_service_base.z.so')
script = script.replace('sha256sum "$p"', 'sha256sum "$source"', 1)
script = script.replace('/busybox cp "$p" "$p.sheng-flag-new"', '/busybox cp "$source" "$p.sheng-flag-new"')
(dest/'apply-rosen-handle.sh').write_bytes(script.encode())

g = (archive/'probe_graphics_v45.inc').read_text()
g = g.replace('    char parent[512];', '    if(!strncmp(target,"/hmos-root/vendor/",18)||!strncmp(target,"/hmos-root/vendor_dlkm/",23)){errno=EROFS;return -1;}\n    char parent[512];', 1)
g = g.replace('/hmos-root/vendor/lib64/libdisplay_composer_vdi_impl.z.so', '/hmos-root/compat/lib64/libdisplay_composer_vdi_impl.z.so')
g = g.replace('/hmos-root/vendor/lib64/passthrough/indirect/libdisplay_buffer_vdi_impl.z.so', '/hmos-root/compat/lib64/libdisplay_buffer_vdi_impl.z.so')
g = g.replace('/hmos-root/vendor/etc/vulkan/icd.d/vulkan_driver_v350.json', '/hmos-root/compat/etc/vulkan/icd.d/sheng-turnip.json')
needle = '    const char *configs[]='
assert needle in g
g = g.replace(needle, '''    if(mkdirs("/hmos-root/compat/lib64")<0||mkdirs("/hmos-root/compat/bin")<0)return -1;
    '''+needle.lstrip(), 1)
# Reuse the bounded shell runner for both guarded runtime patch scripts.
g = g.replace('static int graphics_patch_native_handle(void)', 'static int graphics_run_script(const char *script)')
g = g.replace('"sh","/graphics/apply-rosen-handle.sh",', '"sh",script,')
g = g.replace('    if(graphics_patch_native_handle()<0)return -1;', '''    const char *loader_configs[]={"ld-musl-aarch64.path","ld-musl-namespace-aarch64.ini","ld-musl-namespace-aarch64-New.ini","ld-musl-namespace-aarch64-flex.ini","ld-musl-namespace-aarch64-test.ini"};
    for(unsigned i=0;i<sizeof(loader_configs)/sizeof(loader_configs[0]);i++){
        char source[256],target[256];snprintf(source,sizeof(source),"/graphics/%s",loader_configs[i]);
        snprintf(target,sizeof(target),"/hmos-root/system/etc/%s",loader_configs[i]);
        if(copy_ram_asset(source,target,0644)<0)return -1;
    }
    if(graphics_run_script("/graphics/apply-compat-paths.sh")<0||graphics_run_script("/graphics/apply-rosen-handle.sh")<0)return -1;''')
g = g.replace('original images unchanged', 'vendor mounted read-only; private hardware libraries in /compat')
g = g.replace('snprintf(target,sizeof(target),"/hmos-root/data/local/tmp/sheng-graphics/%s",boot_assets[i]);',
    'snprintf(target,sizeof(target),"/hmos-root/compat/%s/%s",strstr(boot_assets[i],".so")?"lib64":"bin",boot_assets[i]);')
g = g.replace('    if(copy_ram_asset("/graphics/bootanimation-launcher","/hmos-root/system/bin/bootanimation",0755)<0||\n', '    if(')
g = g.replace('/hmos-root/system/lib/firmware/%s', '/hmos-root/compat/firmware/%s')
g = g.replace('closedir(firmware);if(result<0)return -1;',
    'closedir(firmware);if(result<0)return -1;\n    if(put("/sys/module/firmware_class/parameters/path","/hmos-root/compat/firmware")<0)return -1;')
# Diagnostic resource remains at the old test path; executable/library fixes live in /compat.
g = g.replace('    const char *boot_log=',
    '    if(copy_ram_asset("/graphics/bootpic.zip","/hmos-root/data/local/tmp/sheng-graphics/bootpic.zip",0644)<0)return -1;\n    const char *boot_log=')
(r/'tools/probe_graphics.inc').write_text(g, encoding='utf-8')

c = (archive/'hmos_probe_v45.c').read_text().replace('v45', 'v46')
old = 'if(ram_overlay(lower,target,parts[i])<0)return -1;'
assert old in c
c = c.replace(old, '''if(!strcmp(parts[i],"vendor")||!strcmp(parts[i],"vendor_dlkm")){
            if(mkdirs(target)<0||mount(lower,target,0,MS_BIND,0)<0||mount(0,target,0,MS_BIND|MS_REMOUNT|MS_RDONLY|MS_NOSUID,0)<0)return -1;
        }else if(ram_overlay(lower,target,parts[i])<0)return -1;''')
c = c.replace('"/hmos-root/vendor/etc/init",', '')
c = c.replace('char *args[]={"/system/bin/init","--second-stage",NULL};execv(args[0],args);',
              'char *args[]={"/compat/bin/init","--second-stage",NULL};execv(args[0],args);')
assert '/hmos-root/vendor/etc/init' not in c
(r/'tools/hmos_probe.c').write_text(c, encoding='utf-8')
for a,b in [('build_probe_v45.py','build_probe_v46.py'),('verify_v45.py','verify_v46.py')]:
    text = (r/'tools'/a).read_text().replace('v45','v46')
    (r/'tools'/b).write_text(text, encoding='utf-8')
cfg = json.loads((r/'tools/configs/init-core-v45.cfg').read_text())
next(s for s in cfg['services'] if s['name']=='bootanimation')['path'][0] = '/compat/bin/bootanimation-launcher'
(r/'tools/configs/init-core-v46.cfg').write_text(json.dumps(cfg, indent=2)+'\n')
report = {'version':'v46', 'status':'OFFLINE_CANDIDATE_NOT_FLASHED', 'vendor_writes_allowed':False,
          'patches':specs, 'namespace_inputs':namespace_inputs,
          'note':'No vendor image/file/overlay changes; no desktop or cold-boot acceptance inferred.'}
(r/'analysis/v46-compat-layer.json').write_text(json.dumps(report, indent=2)+'\n', encoding='utf-8')
print(json.dumps(report, indent=2))
