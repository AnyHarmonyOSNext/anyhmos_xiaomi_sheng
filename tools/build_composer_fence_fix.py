"""WSL: build one fix and a 10000-frame ownership regression, using pinned inputs."""
from pathlib import Path
import os, runpy, subprocess, json, hashlib, shutil, tarfile
r = Path('/mnt/c/SHENG_WORKSPACE')
base = Path('/root/hmos-work/graphics-deps')
sdk = Path('/root/hmos-work/sdk-6.0.0.47/installed/native')
port = base / 'sheng-graphics-port'
os.environ.update(ANYHARMONYOS_OHOS_SOURCE=str(base / 'source'),
    ANYHARMONYOS_STAGE=str(base / 'stage'),
    ANYHARMONYOS_ROM_SYSTEM_LIBS=str(r / 'work/hmos_system/system/system/lib64'),
    ANYHARMONYOS_SDK=str(sdk))
cfg = runpy.run_path(str(port / 'tools/build_adapter.py'))
common = cfg['COMMON'] + ['-I' + str(port / 'adapter')]
out = r / 'compat/sheng-graphics/fence-v1'
out.mkdir(exist_ok=True)
cpp = cfg['CPP']
drm = base / 'stage/lib/libdrm.a'
report = {}
for version, source in [('baseline', r / 'tools/archive/composer_vdi_v73.cpp'),
                         ('fixed', r / 'compat/sheng-graphics/src/composer_vdi.cpp')]:
    target = out / ('composer_fence_' + version)
    subprocess.run(common + ['-DACE5_VSYNC_TEST', str(source),
        str(r / 'tools/composer_fence_lifecycle.cpp'), str(drm), str(cpp), '-o', str(target)], check=True)
    subprocess.run([str(sdk / 'llvm/bin/llvm-strip'), str(target)], check=True)
    report[target.name] = hashlib.sha256(target.read_bytes()).hexdigest()
target = out / 'libdisplay_composer_vdi_impl.z.so'
subprocess.run(common + ['-shared', '-fPIC', '-Wl,-z,defs', '-Wl,-soname,' + target.name,
    str(r / 'compat/sheng-graphics/src/composer_vdi.cpp'),
    str(port / 'generated/vdi-only/composer_unsupported.cpp'),
    str(drm), str(cpp), '-o', str(target)], check=True)
subprocess.run([str(sdk / 'llvm/bin/llvm-strip'), str(target)], check=True)
report[target.name] = hashlib.sha256(target.read_bytes()).hexdigest()
(out / 'manifest.json').write_text(json.dumps(report, indent=2) + '\n')
with tarfile.open(out / 'fence-tests.tar.gz', 'w:gz') as tar:
    for version in ['baseline', 'fixed']:
        p = out / ('composer_fence_' + version)
        tar.add(p, arcname=p.name)
print(json.dumps(report, indent=2))
