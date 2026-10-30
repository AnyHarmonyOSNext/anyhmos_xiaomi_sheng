"""Instrument the fixed-120Hz v85 backend without changing pacing or ranges."""
from pathlib import Path
import os
import runpy
import subprocess
import hashlib
import json

r = Path('/mnt/c/SHENG_WORKSPACE')
b = Path('/root/hmos-work/graphics-deps')
p = b / 'sheng-graphics-port'
sdk = Path('/root/hmos-work/sdk-6.0.0.47/installed/native')
os.environ.update(ANYHARMONYOS_OHOS_SOURCE=str(b/'source'), ANYHARMONYOS_STAGE=str(b/'stage'),
                 ANYHARMONYOS_ROM_SYSTEM_LIBS=str(r/'work/hmos_system/system/system/lib64'), ANYHARMONYOS_SDK=str(sdk))
cfg = runpy.run_path(str(p/'tools/build_adapter.py'))
out = r / 'compat/sheng-graphics/composer-metrics-v1'
out.mkdir(exist_ok=True)
s = (r/'compat/sheng-graphics/brightness-v1/composer_vdi.cpp').read_text()
s = s.replace('#include <cerrno>', '#include <cerrno>\n#include <cstdarg>')
marker = '// Aggregate only: avoid per-frame logging changing the pacing being measured.'
assert s.count(marker) == 1
s = s.replace(marker, '''void Metric(const char *format, ...)
{
    int saved = errno;
    FILE *file = fopen("/data/local/tmp/sheng-composer-metrics.txt", "ae");
    if (file) {
        fprintf(file, "t_ns=%llu ", (unsigned long long)MonotonicNs());
        va_list args; va_start(args, format); vfprintf(file, format, args); va_end(args);
        fputc('\\n', file); fclose(file);
    }
    errno = saved;
}
''' + marker)
start = s.index('        Ace5Log("submit frames=')
end = s.index('        *this = {};', start)
s = s[:end] + s[start:end].replace('Ace5Log(', 'Metric(', 1) + s[end:]
needle = 'DEVICE_LOCK(id); if(level>255)return INVALID; uint32_t maximum=0;'
assert s.count(needle) == 1
s = s.replace(needle, '''DEVICE_LOCK(id);
    Metric("BACKLIGHT_REQUEST raw=%u supported_max=255", level);
    if(level>255){Metric("BACKLIGHT_REJECT raw=%u",level);return INVALID;}
    uint32_t maximum=0;''')
needle = 'Ace5Log("backlight level=%u native=%u max=%u verified=%u",level,native,maximum,observed);return OK;'
assert s.count(needle) == 1
s = s.replace(needle, 'Metric("BACKLIGHT_APPLIED raw=%u native=%u max=%u verified=%u",level,native,maximum,observed);' + needle)
source = out/'composer_vdi.cpp'
source.write_text(s)
stub = r/'compat/sheng-graphics/brightness-v1/composer_unsupported.cpp'
lib = out/'libdisplay_composer_vdi_impl.z.so'
subprocess.run(cfg['COMMON'] + ['-I'+str(p/'adapter'), '-shared', '-fPIC', '-Wl,-z,defs',
    '-Wl,-soname,'+lib.name, str(source), str(stub), str(b/'stage/lib/libdrm.a'), str(cfg['CPP']), '-o', str(lib)], check=True)
subprocess.run([str(sdk/'llvm/bin/llvm-strip'), str(lib)], check=True)
(out/'manifest.json').write_text(json.dumps({f.name: {'bytes': f.stat().st_size,
    'sha256': hashlib.sha256(f.read_bytes()).hexdigest()} for f in [source, lib]}, indent=2)+'\n')
print((out/'manifest.json').read_text())
