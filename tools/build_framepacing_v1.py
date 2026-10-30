from pathlib import Path
import hashlib,json,os,runpy,subprocess
r=Path(__file__).resolve().parent.parent
b=Path('/root/hmos-work/graphics-deps');p=b/'sheng-graphics-port';sdk=Path('/root/hmos-work/sdk-6.0.0.47/installed/native')
os.environ.update(ANYHARMONYOS_OHOS_SOURCE=str(b/'source'),ANYHARMONYOS_STAGE=str(b/'stage'),ANYHARMONYOS_ROM_SYSTEM_LIBS=str(r/'work/hmos_system/system/system/lib64'),ANYHARMONYOS_SDK=str(sdk))
c=runpy.run_path(str(p/'tools/build_adapter.py'));out=r/'compat/sheng-graphics/framepacing-v1';lib=out/'libdisplay_composer_vdi_impl.z.so'
subprocess.run(c['COMMON']+['-I'+str(p/'adapter'),'-shared','-fPIC','-Wl,-z,defs','-Wl,-soname,'+lib.name,str(out/'composer_vdi.cpp'),str(r/'compat/sheng-graphics/brightness-v1/composer_unsupported.cpp'),str(b/'stage/lib/libdrm.a'),str(c['CPP']),'-o',str(lib)],check=True)
subprocess.run([str(sdk/'llvm/bin/llvm-strip'),str(lib)],check=True)
gpu=out/'sheng_gpu_policy'
subprocess.run([str(sdk/'llvm/bin/clang'),'--target=aarch64-linux-ohos','-std=c11','-O2','-Wall','-Wextra','-Werror','-Wno-misleading-indentation','-I'+str(b/'stage/include/libdrm'),str(out/'sheng_gpu_policy.c'),'-o',str(gpu)],check=True)
subprocess.run([str(sdk/'llvm/bin/llvm-strip'),str(gpu)],check=True)
(out/'manifest.json').write_text(json.dumps({f.name:{'bytes':f.stat().st_size,'sha256':hashlib.sha256(f.read_bytes()).hexdigest()} for f in [out/'composer_vdi.cpp',lib,gpu]},indent=2)+'\n')
print((out/'manifest.json').read_text())
