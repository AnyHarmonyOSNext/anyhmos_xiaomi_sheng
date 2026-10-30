"""Stage existing reference Mesa for an isolated real GPU test, not global EGL."""
from pathlib import Path
import subprocess, tarfile, hashlib, json, io
r=Path(__file__).resolve().parent.parent
b=Path('/root/hmos-work/graphics-deps'); ref=Path('/root/hmos-reference/AnyHarmonyOS/sm8650/graphics-port/gpu-port/src')
sdk=Path('/root/hmos-work/sdk-6.0.0.47/installed/native')
source=(ref/'egl_contract.cpp').read_text().replace('/data/libEGL_impl.so','/data/local/tmp/sheng-zink/libEGL_impl.so').replace('/data/libGLESv2_impl.so','/data/local/tmp/sheng-zink/libGLESv2_impl.so')
src=r/'tools/native_zink_contract_v125.cpp'; src.write_text(source)
out=r/'compat/sheng-graphics/zink-private-v125'; out.mkdir(exist_ok=True)
exe=out/'native_zink_contract'
subprocess.run([str(sdk/'llvm/bin/clang++'),'--target=aarch64-linux-ohos','-std=c++17','-O2','-fno-exceptions','-fno-rtti','-nostdlib++','-include',str(b/'sheng-graphics-port/tests/platform_cpp_config.h'),'-I'+str(ref),str(src),str(b/'rom-link/libc++.so'),'-o',str(exe)],check=True)
subprocess.run([str(sdk/'llvm/bin/llvm-strip'),str(exe)],check=True)
items={'native_zink_contract':exe,'libEGL_impl.so':r/'compat/sheng-graphics/zink-v1/libEGL_impl.so','libGLESv2_impl.so.2':r/'compat/sheng-graphics/zink-v1/libGLESv2_impl.so.2','libGLESv1_CM_impl.so.1':r/'compat/sheng-graphics/zink-v1/libGLESv1_CM_impl.so.1','libgallium-25.0.1.so':r/'compat/sheng-graphics/zink-v1/libgallium-25.0.1.so'}
report={}
with tarfile.open(out/'zink-private-test.tar.gz','w:gz') as tar:
    for name,path in items.items():
        data=path.read_bytes(); assert data[:6]==b'\x7fELF\x02\x01'
        info=tarfile.TarInfo(name); info.size=len(data); info.mode=0o755; info.mtime=0
        tar.addfile(info,io.BytesIO(data)); report[name]=dict(bytes=len(data),sha256=hashlib.sha256(data).hexdigest())
    for name,target in [('libGLESv2_impl.so','libGLESv2_impl.so.2'),('libGLESv1_impl.so','libGLESv1_CM_impl.so.1'),('libGLESv3_impl.so','libGLESv2_impl.so.2')]:
        info=tarfile.TarInfo(name); info.type=tarfile.SYMTYPE; info.linkname=target; info.mode=0o777; tar.addfile(info)
(out/'manifest.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps(report)); print('archive_bytes=',(out/'zink-private-test.tar.gz').stat().st_size)
