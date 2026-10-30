from pathlib import Path
import subprocess, hashlib, json, os, runpy
r = Path('/mnt/c/SHENG_WORKSPACE')
b = Path('/root/hmos-work/graphics-deps')
sdk = Path('/root/hmos-work/sdk-6.0.0.47/installed/native')
out = r / 'compat/sheng-graphics/surface-reclaim-v1'
out.mkdir(exist_ok=True)
lib = out / 'libsheng_surface_diagnostic.so'
subprocess.run([str(sdk / 'llvm/bin/clang++'), '--target=aarch64-linux-ohos',
    '-std=c++17', '-O2', '-Wall', '-Wextra', '-Werror', '-fno-exceptions',
    '-fno-rtti', '-nostdlib++', '-shared', '-fPIC', '-include',
    str(b/'sheng-graphics-port/tests/platform_cpp_config.h'),
    str(r / 'tools/native_surface_reclaim_v1.cpp'),
    str(r / 'tools/native_buffer_import_observer.S'),
    str(r / 'work/donor-hdi-link/libc++.so'), '-o', str(lib)], check=True)
os.environ.update(ANYHARMONYOS_OHOS_SOURCE=str(b/'source'),ANYHARMONYOS_STAGE=str(b/'stage'),ANYHARMONYOS_ROM_SYSTEM_LIBS=str(r/'work/hmos_system/system/system/lib64'),ANYHARMONYOS_SDK=str(sdk))
cfg=runpy.run_path(str(b/'sheng-graphics-port/tools/build_adapter.py'))
fixture=out/'native_surface_reclaim_probe'
subprocess.run(cfg['COMMON']+[str(r/'tools/native_surface_usage_probe.cpp'),str(cfg['CPP']),'-o',str(fixture)],check=True)
report={}
for p in [lib,fixture]:
    subprocess.run([str(sdk / 'llvm/bin/llvm-strip'), str(p)], check=True)
    report[p.name]=dict(bytes=p.stat().st_size, sha256=hashlib.sha256(p.read_bytes()).hexdigest())
(out/'manifest.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps(report))
