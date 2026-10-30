"""Keep native HDI OFF latched across late client-composition submissions."""
from pathlib import Path
import hashlib
import json
import os
import runpy
import subprocess

r = Path(__file__).resolve().parent.parent
b = Path('/root/hmos-work/graphics-deps')
p = b / 'sheng-graphics-port'
sdk = Path('/root/hmos-work/sdk-6.0.0.47/installed/native')
os.environ.update(ANYHARMONYOS_OHOS_SOURCE=str(b/'source'),
                  ANYHARMONYOS_STAGE=str(b/'stage'),
                  ANYHARMONYOS_ROM_SYSTEM_LIBS=str(r/'work/hmos_system/system/system/lib64'),
                  ANYHARMONYOS_SDK=str(sdk))
c = runpy.run_path(str(p/'tools/build_adapter.py'))
out = r/'compat/sheng-power/screen-v145'
out.mkdir(exist_ok=True)
s = (r/'compat/sheng-graphics/framepacing-v1/composer_vdi.cpp').read_text()

def replace(old, new):
    global s
    assert s.count(old) == 1, old
    s = s.replace(old, new)

replace('Buffer client;\n', '''Buffer client;
// Protected by mutex, together with the native power request and every commit.
// Late RS frames must never turn a successfully powered-off panel back on.
bool requestedPowerOn = true;
bool loggedOffSubmission = false;
''')
replace('int Submit(bool testOnly)\n{\n', '''int Submit(bool testOnly)
{
    if (!testOnly && !requestedPowerOn) {
        if (!loggedOffSubmission) {
            Ace5Log("POWER_OFF_LATCH suppressed late frame without DRM commit");
            loggedOffSubmission = true;
        }
        return OK;
    }
''')
replace('    if (active == wanted) return OK;\n    int result;', '''    if (active == wanted) {
        requestedPowerOn = wanted;
        loggedOffSubmission = false;
        return OK;
    }
    const bool previousRequest = requestedPowerOn;
    // ON must be able to submit the retained client buffer. Restore the prior
    // request if the atomic power transition fails, instead of claiming success.
    if (wanted) requestedPowerOn = true;
    int result;''')
replace('    Ace5Log("power requested=%d result=%d", int(status), result);', '''    if (!result) {
        requestedPowerOn = wanted;
        loggedOffSubmission = false;
    } else {
        requestedPowerOn = previousRequest;
    }
    Ace5Log("power requested=%d result=%d latched_on=%d", int(status), result, requestedPowerOn);''')
src = out/'composer_vdi.cpp'
src.write_text(s)
lib = out/'libdisplay_composer_vdi_impl.z.so'
subprocess.run(c['COMMON']+['-I'+str(p/'adapter'),'-shared','-fPIC','-Wl,-z,defs',
    '-Wl,-soname,'+lib.name,str(src),
    str(r/'compat/sheng-graphics/brightness-v1/composer_unsupported.cpp'),
    str(b/'stage/lib/libdrm.a'),str(c['CPP']),'-o',str(lib)],check=True)
subprocess.run([str(sdk/'llvm/bin/llvm-strip'),str(lib)],check=True)
manifest = {f.name:dict(bytes=f.stat().st_size,sha256=hashlib.sha256(f.read_bytes()).hexdigest())
            for f in (src,lib,r/'compat/debug-tools/native_display_wake_v2')}
(out/'power-manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
print(json.dumps(manifest,indent=2))
