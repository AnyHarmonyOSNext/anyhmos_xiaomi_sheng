"""Build isolated mode/backlight support from the verified v82 composer (WSL)."""
from pathlib import Path
import os,runpy,subprocess,re,json,hashlib
r=Path('/mnt/c/SHENG_WORKSPACE')
b=Path('/root/hmos-work/graphics-deps');p=b/'sheng-graphics-port'
sdk=Path('/root/hmos-work/sdk-6.0.0.47/installed/native')
os.environ.update(ANYHARMONYOS_OHOS_SOURCE=str(b/'source'),ANYHARMONYOS_STAGE=str(b/'stage'),ANYHARMONYOS_ROM_SYSTEM_LIBS=str(r/'work/hmos_system/system/system/lib64'),ANYHARMONYOS_SDK=str(sdk))
cfg=runpy.run_path(str(p/'tools/build_adapter.py'))
out=r/'compat/sheng-graphics/brightness-v1';out.mkdir(exist_ok=True)
src=(r/'compat/sheng-graphics/hardware-display-v1/composer_vdi.cpp').read_text()
original=(r/'compat/sheng-graphics/panel-capability-v1/composer_vdi.cpp').read_text()
# Retain the fixed preferred mode exactly as v82. Backlight and property cache only.
a=src.index('extern "C" int32_t GetDisplaySupportedModes(')
z=src.index('extern "C" int32_t GetDisplayPowerStatus(',a)
a0=original.index('extern "C" int32_t GetDisplaySupportedModes(')
z0=original.index('extern "C" int32_t GetDisplayPowerStatus(',a0)
src=src[:a]+original[a0:z0]+src[z:]
source=out/'composer_vdi.cpp';source.write_text(src)
# Regenerate unsupported methods locally, without changing reference build files.
implemented=set(re.findall(r'extern "C" int32_t (\w+)\(',src))
implemented.update(re.findall(r'SETTER\((\w+),',src))
header=(p/'generated/vdi-only/composer_exports.h').read_text()
stubs='#include "composer_exports.h"\nnamespace OHOS::HDI::Display::Composer {\n'
for name,args in re.findall(r'extern "C" int32_t (\w+)\((.*?)\);',header,re.S):
 if name not in implemented:stubs+=f'extern "C" int32_t {name}({args}) {{ return -5; }}\n'
stub=out/'composer_unsupported.cpp';stub.write_text(stubs+'}\n')
lib=out/'libdisplay_composer_vdi_impl.z.so'
subprocess.run(cfg['COMMON']+['-I'+str(p/'adapter'),'-shared','-fPIC','-Wl,-z,defs','-Wl,-soname,'+lib.name,str(source),str(stub),str(b/'stage/lib/libdrm.a'),str(cfg['CPP']),'-o',str(lib)],check=True)
subprocess.run([str(sdk/'llvm/bin/llvm-strip'),str(lib)],check=True)
(out/'manifest.json').write_text(json.dumps({f.name:{'bytes':f.stat().st_size,'sha256':hashlib.sha256(f.read_bytes()).hexdigest()} for f in [source,stub,lib]},indent=2)+'\n')
print((out/'manifest.json').read_text())
