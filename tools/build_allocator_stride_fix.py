"""Build a hardware-compatible pitch for allocations subsequently imported by GPU (WSL)."""
from pathlib import Path
import os,runpy,subprocess,shutil,tarfile,hashlib,json
r=Path('/mnt/c/SHENG_WORKSPACE')
b=Path('/root/hmos-work/graphics-deps'); port=b/'sheng-graphics-port'
sdk=Path('/root/hmos-work/sdk-6.0.0.47/installed/native')
os.environ.update(ANYHARMONYOS_OHOS_SOURCE=str(b/'source'),ANYHARMONYOS_STAGE=str(b/'stage'),
    ANYHARMONYOS_ROM_SYSTEM_LIBS=str(r/'work/hmos_system/system/system/lib64'),ANYHARMONYOS_SDK=str(sdk))
cfg=runpy.run_path(str(port/'tools/build_adapter.py'))
out=r/'compat/sheng-graphics/stride-v1'; out.mkdir(exist_ok=True)
source=(port/'adapter/buffer_vdi.cpp').read_text()
(out/'buffer_vdi.before.cpp').write_text(source)
old='''    stride = (usage & PREFER_NO_PADDING) ? width * bpp :
        (width * bpp + STRIDE_ALIGNMENT - 1) & ~(STRIDE_ALIGNMENT - 1);'''
assert source.count(old)==1
source=source.replace(old,'''    // CPU-decoded images can later become GPU textures. PREFER_NO_PADDING
    // is a preference; preserve the linear GPU pitch requirement in all RGB/YUV buffers.
    stride = (width * bpp + STRIDE_ALIGNMENT - 1) & ~(STRIDE_ALIGNMENT - 1);''')
(out/'buffer_vdi.cpp').write_text(source)
commands=[('libdisplay_buffer_vdi_impl.z.so',cfg['COMMON']+['-I'+str(port/'adapter'),'-DACE5_LINEAR_STRIDE_ALIGNMENT=128',
    '-shared','-fPIC','-Wl,-z,defs','-Wl,-soname,libdisplay_buffer_vdi_impl.z.so',str(out/'buffer_vdi.cpp')]),
    ('allocator_native_import',cfg['COMMON']+[str(r/'tools/allocator_native_import.cpp')])]
report={}
for name,command in commands:
    target=out/name
    subprocess.run(command+[str(cfg['CPP']),'-o',str(target)],check=True)
    subprocess.run([str(sdk/'llvm/bin/llvm-strip'),str(target)],check=True)
    report[name]=dict(bytes=target.stat().st_size,sha256=hashlib.sha256(target.read_bytes()).hexdigest())
with tarfile.open(out/'stride-test.tar.gz','w:gz') as tar:
    for name in report:tar.add(out/name,arcname=name)
(out/'manifest.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps(report))
