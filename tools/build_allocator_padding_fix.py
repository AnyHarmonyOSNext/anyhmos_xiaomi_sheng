"""Build the v76 allocator with enough backing rows for the real GPU layout (WSL)."""
from pathlib import Path
import os, runpy, subprocess, hashlib, json, tarfile

r = Path('/mnt/c/SHENG_WORKSPACE')
b = Path('/root/hmos-work/graphics-deps')
port = b / 'sheng-graphics-port'
sdk = Path('/root/hmos-work/sdk-6.0.0.47/installed/native')
os.environ.update(ANYHARMONYOS_OHOS_SOURCE=str(b/'source'), ANYHARMONYOS_STAGE=str(b/'stage'),
    ANYHARMONYOS_ROM_SYSTEM_LIBS=str(r/'work/hmos_system/system/system/lib64'), ANYHARMONYOS_SDK=str(sdk))
cfg = runpy.run_path(str(port/'tools/build_adapter.py'))
out = r/'compat/sheng-graphics/padding-v1'
out.mkdir(exist_ok=True)
source = (r/'compat/sheng-graphics/stride-v1/buffer_vdi.cpp').read_text()
old = '    size = uint64_t(stride) * height;\n    if (yuv) size += uint64_t(stride) * (height / 2);'
assert source.count(old) == 1
source = source.replace(old, '''    // Turnip's linear RGB layout pads the backing slice to four rows.
    // Keep visible dimensions unchanged; allocate the complete backing slice.
    const uint32_t backingHeight = yuv ? height : (height + 3) & ~3U;
    size = uint64_t(stride) * backingHeight;
    if (yuv) size += uint64_t(stride) * (height / 2);''')
source = source.replace('    // Honor the former even in builds whose default RGB stride is aligned.\n', '')
(out/'buffer_vdi.cpp').write_text(source)
test = (r/'tools/allocator_native_import.cpp').read_text()
test = test.replace('{325,323},{3048,2032}', '{325,323},{842,210},{1,1},{33,2},{1025,7},{3048,2032}')
test = test.replace('cases=4', 'cases=8')
(out/'allocator_native_import.cpp').write_text(test)
commands = [
    ('libdisplay_buffer_vdi_impl.z.so', cfg['COMMON']+['-I'+str(port/'adapter'), '-DACE5_LINEAR_STRIDE_ALIGNMENT=128',
        '-shared', '-fPIC', '-Wl,-z,defs', '-Wl,-soname,libdisplay_buffer_vdi_impl.z.so', str(out/'buffer_vdi.cpp')]),
    ('allocator_native_import', cfg['COMMON']+[str(out/'allocator_native_import.cpp')]),
]
report = {}
for name, command in commands:
    target = out/name
    subprocess.run(command+[str(cfg['CPP']), '-o', str(target)], check=True)
    subprocess.run([str(sdk/'llvm/bin/llvm-strip'), str(target)], check=True)
    report[name] = dict(bytes=target.stat().st_size, sha256=hashlib.sha256(target.read_bytes()).hexdigest())
with tarfile.open(out/'padding-test.tar.gz', 'w:gz') as tar:
    for name in report:
        tar.add(out/name, arcname=name)
(out/'manifest.json').write_text(json.dumps(report, indent=2)+'\n')
print(json.dumps(report))
