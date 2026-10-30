"""Build pinned reference Mesa in private WSL tree; never modifies donor ROM."""
from pathlib import Path
import subprocess,shutil,json,os,sys
base=Path('/root/hmos-work/graphics-deps');mesa=base/'source/mesa3d'
ref=Path('/root/hmos-reference/AnyHarmonyOS');gpu=ref/'sm8650/graphics-port/gpu-port'
workspace=Path('/mnt/c/SHENG_WORKSPACE')
sdk=Path(json.loads(Path('/root/hmos-work/sdk-6.0.0.47/installation.json').read_text())['sdk'])
romlink=base/'rom-link';romlink.mkdir(exist_ok=True)
for item in (workspace/'work/donor-hdi-link').iterdir():
    if item.is_file():shutil.copy2(item,romlink/item.name)
for name in ['tu_ohos.cc','tu_ohos.h']:shutil.copy2(gpu/'src'/name,mesa/'src/freedreno/vulkan'/name)
for kind in ['turnip','zink']:
    text=(gpu/f'ohos-{kind}.example.ini').read_text()
    for old,new in [('/opt/anyharmonyos-deps/ohos-sdk/native',str(sdk)),('/opt/anyharmonyos-deps/stage',str(base/'stage')),('/opt/anyharmonyos-deps/source',str(base/'source')),('/opt/anyharmonyos-deps/rom/system/lib64/chipset-sdk-sp/libnative_buffer.so',str(workspace/'work/donor-hdi-link/libsurface.z.so')),('/opt/anyharmonyos-deps/rom/system/lib64/chipset-sdk-sp/libhilog.so',str(workspace/'work/donor-hdi-link/libhilog.so')),('/opt/anyharmonyos-deps/rom/system/lib64/chipset-sdk-sp/libc++.so',str(workspace/'work/donor-hdi-link/libc++.so')),('/opt/AnyHarmonyOS',str(ref))]:text=text.replace(old,new)
    text=text.replace(str(workspace/'work/donor-hdi-link'),str(romlink))
    (base/f'{kind}.ini').write_text(text)
    # Both original native_buffer/native_window aliases resolve to libsurface.
    text=text.replace('/opt/anyharmonyos-deps/rom/system/lib64/chipset-sdk-sp/libnative_window.so',str(workspace/'work/donor-hdi-link/libsurface.z.so'))
    text=text.replace(str(workspace/'work/donor-hdi-link'),str(romlink))
    (base/f'{kind}.ini').write_text(text)
env=os.environ.copy();env.update(PKG_CONFIG_LIBDIR=str(base/'stage/lib/pkgconfig'),PKG_CONFIG_PATH='',PATH=str(base/'mesa-build-env/bin')+':'+env['PATH'])
pc=base/'stage/lib/pkgconfig/libhilog.pc'
pc.write_text('Name: libhilog\nDescription: Actual donor OHOS hilog ELF\nVersion: 1.0\nLibs: -L'+str(romlink)+' -lhilog\nCflags: -I'+str(base/'source/hiviewdfx_hilog/interfaces/native/innerkits/include')+'\n')
(base/'stage/lib/pkgconfig/libsurface.pc').write_text('Name: libsurface\nDescription: Actual donor native window/buffer ELF\nVersion: 1.0\nLibs: '+str(romlink/'libsurface.z.so')+'\nCflags: -I'+str(sdk/'sysroot/usr/include/native_window')+'\n')
kind=sys.argv[1] if len(sys.argv)>1 else 'turnip';assert kind in ['turnip','zink'];build=base/f'{kind}-build'
if not (build/'build.ninja').exists():
    options=['-Dplatforms=','-Dvulkan-drivers=freedreno','-Dfreedreno-kmds=kgsl','-Dgallium-drivers=','-Degl=disabled','-Dgles1=disabled','-Dgles2=disabled','-Dopengl=false'] if kind=='turnip' else ['-Dplatforms=ohos','-Dvulkan-drivers=','-Dgallium-drivers=zink','-Degl=enabled','-Dgles1=enabled','-Dgles2=enabled','-Dopengl=true','-Dgbm=disabled','-Degl-lib-suffix=_impl','-Dgles-lib-suffix=_impl']
    subprocess.run(['meson','setup',str(build),str(mesa),'--cross-file',str(base/f'{kind}.ini'),'--buildtype=release','--wrap-mode=nofallback']+options+['-Dglx=disabled','-Dllvm=disabled','-Dshader-cache=disabled','-Dzstd=disabled','-Dexpat=disabled'],check=True,env=env)
subprocess.run(['meson','compile','-C',str(build),'-j','8'],check=True,env=env)
