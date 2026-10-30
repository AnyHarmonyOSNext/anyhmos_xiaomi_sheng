from pathlib import Path
import hashlib, json, os, runpy, subprocess
r=Path('/mnt/c/SHENG_WORKSPACE')
b=Path('/root/hmos-work/graphics-deps');sdk=Path('/root/hmos-work/sdk-6.0.0.47/installed/native')
os.environ.update(ANYHARMONYOS_OHOS_SOURCE=str(b/'source'),ANYHARMONYOS_STAGE=str(b/'stage'),ANYHARMONYOS_ROM_SYSTEM_LIBS=str(r/'work/hmos_system/system/system/lib64'),ANYHARMONYOS_SDK=str(sdk))
cfg=runpy.run_path(str(b/'sheng-graphics-port/tools/build_adapter.py'))
out=r/'compat/debug-tools/native_blob_import_contract'
subprocess.run(cfg['COMMON']+['-I'+str(b/'source/mesa3d/include'),str(r/'tools/native_blob_import_contract.cpp'),str(cfg['CPP']),'-ldl','-o',str(out)],check=True)
subprocess.run([str(sdk/'llvm/bin/llvm-strip'),str(out)],check=True)
print(json.dumps(dict(bytes=out.stat().st_size,sha256=hashlib.sha256(out.read_bytes()).hexdigest())))
