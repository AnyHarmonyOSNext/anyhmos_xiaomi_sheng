"""Build isolated sheng display adapters from the pinned public reference.

WSL only. This stages individual adapters/contracts, not a complete ROM/HDF
candidate; the reference's full-candidate input checks are not bypassed.
"""
from pathlib import Path
import hashlib
import json
import os
import shutil
import subprocess
import runpy
import sys
import re

base=Path('/root/hmos-work/graphics-deps')
label=sys.argv[1] if len(sys.argv)>1 else 'v25'
assert re.fullmatch(r'v[0-9]+',label)
sdk=Path(json.loads(Path('/root/hmos-work/sdk-6.0.0.47/installation.json').read_text())['sdk'])
stage=base/'stage'
cross=base/'ohos.ini'
cross.write_text(f'''[binaries]
c = '{sdk}/llvm/bin/clang'
cpp = '{sdk}/llvm/bin/clang++'
ar = '{sdk}/llvm/bin/llvm-ar'
strip = '{sdk}/llvm/bin/llvm-strip'
pkgconfig = 'pkg-config'
[host_machine]
system = 'linux'
cpu_family = 'aarch64'
cpu = 'armv8-a'
endian = 'little'
[properties]
needs_exe_wrapper = true
pkg_config_libdir = ['{stage}/lib/pkgconfig']
[built-in options]
c_args = ['--target=aarch64-linux-ohos']
cpp_args = ['--target=aarch64-linux-ohos']
c_link_args = ['--target=aarch64-linux-ohos']
cpp_link_args = ['--target=aarch64-linux-ohos']
''')
env=os.environ.copy()
env.update(PKG_CONFIG_LIBDIR=str(stage/'lib/pkgconfig'),PKG_CONFIG_PATH='')
build=base/'libdrm-build'
if not (build/'build.ninja').exists():
    subprocess.run(['meson','setup',str(build),str(base/'libdrm-2.4.124'),'--cross-file',str(cross),'--prefix='+str(stage),'--libdir=lib','--buildtype=release','-Ddefault_library=both',
        '-Dintel=disabled','-Dradeon=disabled','-Damdgpu=disabled','-Dnouveau=disabled','-Dvmwgfx=disabled','-Dfreedreno=disabled','-Dvc4=disabled','-Detnaviv=disabled','-Dtests=false','-Dudev=false','-Dman-pages=disabled','-Dvalgrind=disabled'],check=True,env=env)
subprocess.run(['meson','compile','-C',str(build),'-j','8'],check=True,env=env)
subprocess.run(['meson','install','-C',str(build)],check=True,env=env)
reference=Path('/root/hmos-reference/AnyHarmonyOS/sm8650/graphics-port')
port=base/'sheng-graphics-port'
if not port.exists():
    shutil.copytree(reference,port)
    script=port/'tools/build_adapter.py'
    text=script.read_text().replace('-DACE5_LINEAR_STRIDE_ALIGNMENT=64','-DACE5_LINEAR_STRIDE_ALIGNMENT=128')
    script.write_text(text)
    (port/'SHENG-NOTES.md').write_text('Private SM8550 trial copy from AnyHarmonyOS cb1ce16.\nLinear stride alignment=128, verified stock dumb pitch12288 for3048x2032.\nNo complete HDF payload or full ROM candidate is claimed. Native contracts required.\n')
for file in [port/'adapter/composer_vdi.cpp',port/'tests/composer_vdi_contract.cpp']:
    file.write_text(file.read_text().replace('"Ace5 DSI"','"Sheng DSI"'))
workspace=Path('/mnt/c/SHENG_WORKSPACE')
subprocess.run(['python3',str(workspace/'tools/patch_sheng_split_display.py')],check=True)
rom=workspace/'work/hmos_system/system/system/lib64'
cpp=rom/'chipset-sdk-sp/libc++.so'
assert cpp.is_file(),cpp
env.update(ANYHARMONYOS_SDK=str(sdk),ANYHARMONYOS_STAGE=str(stage),ANYHARMONYOS_OHOS_SOURCE=str(base/'source'),ANYHARMONYOS_ROM_SYSTEM_LIBS=str(rom))
subprocess.run(['python3',str(port/'tools/build_adapter.py')],check=True,env=env)
subprocess.run([str(sdk/'llvm/bin/clang++'),'--target=aarch64-linux-ohos','-std=c++17','-O2','-fno-exceptions','-fno-rtti','-nostdlib++','-include',str(port/'tests/platform_cpp_config.h'),str(port/'tests/platform_cpp_abi.cpp'),str(cpp),'-o',str(port/'out/platform_cpp_abi')],check=True,env=env)
os.environ.update({k:v for k,v in env.items() if k.startswith('ANYHARMONYOS_')})
builder=runpy.run_path(str(port/'tools/build_adapter.py'))
builder['build'](str(workspace/'tools/sheng_display_scanout.cpp'),'sheng_display_scanout')
builder['build'](str(workspace/'tools/sheng_kms_diagnostic.cpp'),'sheng_kms_diagnostic',extra=[str(stage/'lib/libdrm.a')])
outputs=[]
for file in (port/'out').iterdir():
    if file.is_file():
        outputs.append({'file':str(file),'bytes':file.stat().st_size,'sha256':hashlib.sha256(file.read_bytes()).hexdigest(),'elf':subprocess.check_output([str(sdk/'llvm/bin/llvm-readelf'),'-h','-d',str(file)],text=True)})
(base/'build-report.json').write_text(json.dumps({'reference_commit':'cb1ce16','stride_alignment':128,'rom_cpp_sha256':hashlib.sha256(cpp.read_bytes()).hexdigest(),'files':outputs},indent=2)+'\n')
print('Adapters built:',[x['file'] for x in outputs])
destination=workspace/'compat/sheng-graphics'/label
destination.mkdir(parents=True,exist_ok=True)
for file in (port/'out').iterdir():
    if file.is_file():
        shutil.copy2(file,destination/file.name)
shutil.copy2(base/'build-report.json',workspace/f'analysis/sheng-graphics-{label}-build.json')
