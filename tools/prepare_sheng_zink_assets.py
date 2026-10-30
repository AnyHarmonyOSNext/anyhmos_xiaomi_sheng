"""Stage real AArch64 Mesa outputs and bounded EGL contract; no device action."""
from pathlib import Path
import subprocess,json,hashlib,shutil,gzip
base=Path('/root/hmos-work/graphics-deps');ref=Path('/root/hmos-reference/AnyHarmonyOS')
workspace=Path('/mnt/c/SHENG_WORKSPACE')
sdk=Path(json.loads(Path('/root/hmos-work/sdk-6.0.0.47/installation.json').read_text())['sdk'])
dest=workspace/'compat/sheng-graphics/zink-v1';dest.mkdir(exist_ok=True)
files={'libEGL_impl.so':'src/egl/libEGL_impl.so','libGLESv2_impl.so.2':'src/mapi/es2api/libGLESv2_impl.so.2.0.0','libGLESv1_CM_impl.so.1':'src/mapi/es1api/libGLESv1_CM_impl.so.1.1.0','libgallium-25.0.1.so':'src/gallium/targets/dri/libgallium-25.0.1.so'}
for name,path in files.items():
    target=dest/name;shutil.copy2(base/'zink-build'/path,target)
    subprocess.run([str(sdk/'llvm/bin/llvm-strip'),str(target)],check=True)
gpu=ref/'sm8650/graphics-port/gpu-port/src'
contract=dest/'egl_contract'
subprocess.run([str(sdk/'llvm/bin/clang++'),'--target=aarch64-linux-ohos','-std=c++17','-O2','-fno-exceptions','-fno-rtti','-nostdlib++','-include',str(base/'sheng-graphics-port/tests/platform_cpp_config.h'),'-I'+str(gpu),str(gpu/'egl_contract.cpp'),str(base/'rom-link/libc++.so'),'-o',str(contract)],check=True)
subprocess.run([str(sdk/'llvm/bin/llvm-strip'),str(contract)],check=True)
report={'mesa_commit':subprocess.check_output(['git','-C',str(base/'source/mesa3d'),'rev-parse','HEAD'],text=True).strip(),'status':'built_only_not_device_tested','files':[]}
for file in dest.iterdir():
    data=file.read_bytes();assert data[:6]==b'\x7fELF\x02\x01'
    report['files'].append({'file':file.name,'bytes':len(data),'sha256':hashlib.sha256(data).hexdigest(),'gzip_bytes':len(gzip.compress(data,mtime=0)),'elf':subprocess.check_output([str(sdk/'llvm/bin/llvm-readelf'),'-h','-d',str(file)],text=True)})
(workspace/'analysis/sheng-zink-v1-build.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps([{k:v for k,v in i.items() if k!='elf'} for i in report['files']],indent=2))
