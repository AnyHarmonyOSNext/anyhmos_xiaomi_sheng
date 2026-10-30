"""Read-only inspection of the exact donor loader inputs."""
from pathlib import Path
import hashlib, json, re, struct

root = Path(__file__).resolve().parent.parent
inputs = {
    'init': root/'work/hmos_system/system/system/bin/init',
    'vulkan': root/'work/donor-hdi-link/libvulkan.so',
    'composer': root/'work/vendor-reference-readonly/vendor/lib64/libdisplay_composer_service_1.5.z.so',
    'allocator': root/'work/vendor-reference-readonly/vendor/lib64/liballocator_service_1.0.z.so',
}
needles = [b'etc/init\0', b'/system/etc:/vendor/etc\0', b'/vendor/etc/vulkan/icd.d\0',
           b'libdisplay_composer_vdi_impl.z.so\0', b'libdisplay_buffer_vdi_impl.z.so\0']
report = {}
for name, path in inputs.items():
    raw = path.read_bytes()
    assert raw[:6] == b'\x7fELF\x02\x01'
    strings = []
    for m in re.finditer(rb'[\x20-\x7e]{5,}\x00', raw):
        s = m.group()[:-1].decode()
        if ('libdisplay_' in s and 'vdi' in s) or s in ('etc/init', '/system/etc:/vendor/etc'):
            strings.append({'offset': m.start(), 'string': s})
    matches = {}
    for needle in needles:
        positions = [m.start() for m in re.finditer(re.escape(needle), raw)]
        if positions:
            matches[needle[:-1].decode()] = positions
    report[name] = {'path': str(path.relative_to(root)), 'bytes': len(raw),
                    'sha256': hashlib.sha256(raw).hexdigest(), 'matches': matches, 'strings': strings}
(root/'analysis/compat-loader-inputs.json').write_text(json.dumps(report, indent=2)+'\n', encoding='utf-8')
print(json.dumps(report, indent=2))
