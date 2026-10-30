"""Build the existing composer with the interface value observed by donor RS (WSL)."""
from pathlib import Path
import os, runpy, subprocess, hashlib, json
r=Path('/mnt/c/SHENG_WORKSPACE')
b=Path('/root/hmos-work/graphics-deps'); port=b/'sheng-graphics-port'
sdk=Path('/root/hmos-work/sdk-6.0.0.47/installed/native')
os.environ.update(ANYHARMONYOS_OHOS_SOURCE=str(b/'source'),ANYHARMONYOS_STAGE=str(b/'stage'),
    ANYHARMONYOS_ROM_SYSTEM_LIBS=str(r/'work/hmos_system/system/system/lib64'),ANYHARMONYOS_SDK=str(sdk))
cfg=runpy.run_path(str(port/'tools/build_adapter.py'))
out=r/'compat/sheng-graphics/panel-capability-v1'; out.mkdir(exist_ok=True)
src=(r/'compat/sheng-graphics/src/composer_vdi.cpp').read_text()
old='info.type = V::DISP_INTF_MIPI;'
assert src.count(old)==1
src=src.replace(old, '''// The donor directly casts the HDI value to GraphicInterfaceType, which
    // includes UNKNOWN=0. Its live dump identified 9 as VGA; MIPI is 10.
    info.type = static_cast<decltype(info.type)>(10);''')
(out/'composer_vdi.cpp').write_text(src)
lib=out/'libdisplay_composer_vdi_impl.z.so'
subprocess.run(cfg['COMMON']+['-I'+str(port/'adapter'),'-shared','-fPIC','-Wl,-z,defs',
    '-Wl,-soname,'+lib.name,str(out/'composer_vdi.cpp'),
    str(port/'generated/vdi-only/composer_unsupported.cpp'),str(b/'stage/lib/libdrm.a'),str(cfg['CPP']),'-o',str(lib)],check=True)
subprocess.run([str(sdk/'llvm/bin/llvm-strip'),str(lib)],check=True)
print(json.dumps(dict(bytes=lib.stat().st_size,sha256=hashlib.sha256(lib.read_bytes()).hexdigest())))
