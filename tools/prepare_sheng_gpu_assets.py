"""Pinned Mesa and reference contracts, OHOS ABI, private outputs only (WSL)."""
from pathlib import Path
import subprocess,json,shutil,hashlib,tempfile,gzip
base=Path('/root/hmos-work/graphics-deps');ref=Path('/root/hmos-reference/AnyHarmonyOS')
workspace=Path('/mnt/c/SHENG_WORKSPACE')
sdk=Path(json.loads(Path('/root/hmos-work/sdk-6.0.0.47/installation.json').read_text())['sdk'])
dest=workspace/'compat/sheng-graphics/gpu-v1';dest.mkdir(exist_ok=True)
lib=dest/'libvulkan_freedreno.so'
shutil.copy2(base/'turnip-build/src/freedreno/vulkan/libvulkan_freedreno.so',lib)
subprocess.run([str(sdk/'llvm/bin/llvm-strip'),str(lib)],check=True)
common=[str(sdk/'llvm/bin/clang++'),'--target=aarch64-linux-ohos','-std=c++17','-O2','-fno-exceptions','-fno-rtti','-nostdlib++','-include',str(base/'sheng-graphics-port/tests/platform_cpp_config.h')]
cpp=workspace/'work/donor-hdi-link/libc++.so'
gpu=ref/'sm8650/graphics-port/gpu-port/src'
with tempfile.TemporaryDirectory(prefix='sheng-gpu-') as t:
    td=Path(t)
    for name,array,output in [('fullscreen.vert','vertex_spv','vertex.inc'),('solid.frag','fragment_spv','fragment.inc')]:subprocess.run(['glslangValidator','-V','--vn',array,'-o',str(td/output),str(gpu/name)],check=True)
    for src in ['native_buffer_contract','rosen_gpu_contract']:
        subprocess.run(common+['-I'+str(td),str(gpu/(src+'.cpp')),str(cpp),'-o',str(dest/src)],check=True)
        subprocess.run([str(sdk/'llvm/bin/llvm-strip'),str(dest/src)],check=True)
report={'mesa_commit':subprocess.check_output(['git','-C',str(base/'source/mesa3d'),'rev-parse','HEAD'],text=True).strip(),'files':[]}
for file in dest.iterdir():
    data=file.read_bytes();report['files'].append({'name':file.name,'bytes':len(data),'sha256':hashlib.sha256(data).hexdigest(),'gzip_bytes':len(gzip.compress(data,mtime=0)),'elf':subprocess.check_output([str(sdk/'llvm/bin/llvm-readelf'),'-h','-d',str(file)],text=True)})
(workspace/'analysis/sheng-gpu-v1-build.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps([{k:v for k,v in x.items() if k!='elf'} for x in report['files']],indent=2))
