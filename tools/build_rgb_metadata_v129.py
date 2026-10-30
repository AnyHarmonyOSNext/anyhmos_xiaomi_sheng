"""Extend the existing real shared metadata store to pixel RGB allocations.

BLOB remains byte storage. No metadata values or unsupported keys are faked.
Run under the existing WSL build environment.
"""
from pathlib import Path
import hashlib
import json
import os
import runpy
import subprocess

r = Path(__file__).resolve().parent.parent
b = Path('/root/hmos-work/graphics-deps')
port = b / 'sheng-graphics-port'
sdk = Path('/root/hmos-work/sdk-6.0.0.47/installed/native')
out = r / 'compat/sheng-graphics/rgb-metadata-v129'
out.mkdir(exist_ok=True)
s = (r / 'compat/sheng-graphics/planar-v127/buffer_vdi.cpp').read_text()
changes = {
    '// The pixel allocation retains its original stride and offsets. Only new YUV\n// buffers carry one extra, page-aligned CPU metadata page, outside all pixels.':
    '// The pixel allocation retains its original stride and offsets. New RGB/YUV\n// pixel buffers carry a page-aligned CPU metadata page, outside all pixels.',
    '!Valid(h) || !IsYuv420(h.format) ||': '!Valid(h) || h.format == 38 ||',
    'if (IsYuv420(info.format)) size += 4096;': 'if (info.format != 38) size += 4096;',
    'if (IsYuv420(info.format)) {\n            void *p = mmap':
    'if (info.format != 38) {\n            void *p = mmap',
}
for old, new in changes.items():
    assert s.count(old) == 1, old
    s = s.replace(old, new)
(out / 'buffer_vdi.cpp').write_text(s)
os.environ.update(
    ANYHARMONYOS_OHOS_SOURCE=str(b / 'source'),
    ANYHARMONYOS_STAGE=str(b / 'stage'),
    ANYHARMONYOS_ROM_SYSTEM_LIBS=str(r / 'work/hmos_system/system/system/lib64'),
    ANYHARMONYOS_SDK=str(sdk),
)
cfg = runpy.run_path(str(port / 'tools/build_adapter.py'))
report = {}
for name, args in [
    ('libdisplay_buffer_vdi_impl.z.so', ['-DACE5_LINEAR_STRIDE_ALIGNMENT=128',
     '-shared', '-fPIC', '-Wl,-z,defs', '-Wl,-soname,libdisplay_buffer_vdi_impl.z.so',
     str(out / 'buffer_vdi.cpp')]),
    ('rgb_metadata_probe', [str(r / 'tools/rgb_metadata_probe_v129.cpp')]),
]:
    target = out / name
    subprocess.run(cfg['COMMON'] + ['-I' + str(port / 'adapter')] + args +
                   [str(cfg['CPP']), '-o', str(target)], check=True)
    subprocess.run([str(sdk / 'llvm/bin/llvm-strip'), str(target)], check=True)
    report[name] = dict(bytes=target.stat().st_size,
                       sha256=hashlib.sha256(target.read_bytes()).hexdigest())
(out / 'manifest.json').write_text(json.dumps(report, indent=2) + '\n')
print(json.dumps(report))
