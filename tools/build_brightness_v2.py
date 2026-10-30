"""Use the measured 16-bit donor HDI unit, retain physical 12-bit readback."""
from pathlib import Path
import hashlib
import json
import os
import runpy
import subprocess

r = Path('/mnt/c/SHENG_WORKSPACE')
b = Path('/root/hmos-work/graphics-deps')
p = b/'sheng-graphics-port'
sdk = Path('/root/hmos-work/sdk-6.0.0.47/installed/native')
os.environ.update(ANYHARMONYOS_OHOS_SOURCE=str(b/'source'), ANYHARMONYOS_STAGE=str(b/'stage'),
                 ANYHARMONYOS_ROM_SYSTEM_LIBS=str(r/'work/hmos_system/system/system/lib64'), ANYHARMONYOS_SDK=str(sdk))
cfg = runpy.run_path(str(p/'tools/build_adapter.py'))
out = r/'compat/sheng-graphics/brightness-v2'
out.mkdir(exist_ok=True)
s = (r/'compat/sheng-graphics/composer-metrics-v1/composer_vdi.cpp').read_text()
changes = {
    '// Framework display.para defines 0..255; panel sysfs reports its native scale.':
    '// Donor UI is 0..255; its display pipeline sends a distinct 0..65535 HDI unit.\n// Verified original LUT has 65535 entries and real UI requests exceed 255.',
    'level=(uint64_t(native)*255+maximum/2)/maximum;': 'level=(uint64_t(native)*65535+maximum/2)/maximum;',
    'BACKLIGHT_REQUEST raw=%u supported_max=255': 'BACKLIGHT_REQUEST raw=%u supported_max=65535',
    'if(level>255){Metric(': 'if(level>65535){Metric(',
    'native=(uint64_t(level)*maximum+127)/255;': 'native=(uint64_t(level)*maximum+32767)/65535;',
}
for old,new in changes.items():
    assert s.count(old) == 1, old
    s = s.replace(old,new)
# Inter-frame bins measure active motion separately from long idle gaps.
needle = '    uint64_t begin = 0, frames = 0, sum[5]{}, maximum = 0, slow = 0;'
assert s.count(needle) == 1
s = s.replace(needle, needle+'\n    uint64_t last = 0, gaps[8]{};')
needle = '        if (!begin) begin = t[0];'
s = s.replace(needle, '''        if (last) {
            uint64_t gap = t[5] - last;
            const uint64_t limits[] = {8000000,12000000,17000000,25000000,34000000,50000000,100000000};
            unsigned bin = 0; while (bin < 7 && gap > limits[bin]) ++bin;
            ++gaps[bin];
        }
        last = t[5];
''' + needle)
needle = '        *this = {};'
assert s.count(needle) == 1
s = s.replace(needle, '''        Metric("FRAME_GAPS bins_ms=le8,le12,le17,le25,le34,le50,le100,gt100 counts=%llu,%llu,%llu,%llu,%llu,%llu,%llu,%llu",
            (unsigned long long)gaps[0],(unsigned long long)gaps[1],(unsigned long long)gaps[2],(unsigned long long)gaps[3],
            (unsigned long long)gaps[4],(unsigned long long)gaps[5],(unsigned long long)gaps[6],(unsigned long long)gaps[7]);
        uint64_t previous = last;
        *this = {};
        last = previous;''')
source = out/'composer_vdi.cpp'
source.write_text(s)
lib = out/'libdisplay_composer_vdi_impl.z.so'
subprocess.run(cfg['COMMON'] + ['-I'+str(p/'adapter'), '-shared','-fPIC','-Wl,-z,defs',
    '-Wl,-soname,'+lib.name,str(source),str(r/'compat/sheng-graphics/brightness-v1/composer_unsupported.cpp'),
    str(b/'stage/lib/libdrm.a'),str(cfg['CPP']),'-o',str(lib)], check=True)
subprocess.run([str(sdk/'llvm/bin/llvm-strip'),str(lib)], check=True)
(out/'manifest.json').write_text(json.dumps({x.name:{'bytes':x.stat().st_size,
    'sha256':hashlib.sha256(x.read_bytes()).hexdigest()} for x in [source,lib]}, indent=2)+'\n')
print((out/'manifest.json').read_text())
