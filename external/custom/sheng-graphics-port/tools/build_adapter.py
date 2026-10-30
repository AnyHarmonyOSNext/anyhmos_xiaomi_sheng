#!/usr/bin/env python3
"""Build against official HDI headers and the ROM's original platform libc++."""
from pathlib import Path
import subprocess, os

ROOT = Path(__file__).resolve().parents[1]
SOURCE = Path(os.environ['ANYHARMONYOS_OHOS_SOURCE'])
STAGE = Path(os.environ['ANYHARMONYOS_STAGE'])
ROM = Path(os.environ['ANYHARMONYOS_ROM_SYSTEM_LIBS'])
SDK = Path(os.environ['ANYHARMONYOS_SDK'])
OUT = ROOT / 'out'
CPP = ROM / 'chipset-sdk-sp/libc++.so'
COMMON = [str(SDK / 'llvm/bin/clang++'), '--target=aarch64-linux-ohos',
    '-std=c++17', '-O2', '-g', '-fno-exceptions', '-fno-rtti', '-nostdlib++',
    '-include', str(ROOT / 'tests/platform_cpp_config.h'),
    '-I' + str(ROOT / 'generated/vdi-only'),
    '-I' + str(ROOT / 'generated'),
    '-I' + str(ROOT / 'generated/display/buffer'),
    '-I' + str(SOURCE / 'drivers_hdf_core/interfaces/inner_api/hdi/base'),
    '-I' + str(SOURCE / 'drivers_peripheral/display/buffer/hdi_service/include'),
    '-I' + str(SOURCE / 'drivers_interface/display/composer/common/include'),
    '-I' + str(SOURCE / 'hiviewdfx_hilog/interfaces/native/innerkits/include'),
    '-I'+str(STAGE/'include'),
    '-I'+str(STAGE/'include/libdrm')]

def build(source, output, shared=False, extra=()):
    command = COMMON + (['-shared', '-fPIC', '-Wl,-z,defs',
        '-Wl,-soname,' + output] if shared else [])
    command += [str(ROOT / source)] + list(extra) + [str(CPP), '-o', str(OUT / output)]
    subprocess.run(command, check=True)

if __name__ == '__main__':
    OUT.mkdir(exist_ok=True)
    build('adapter/buffer_vdi.cpp', 'libdisplay_buffer_vdi_impl.z.so', True, ['-DACE5_LINEAR_STRIDE_ALIGNMENT=128'])
    build('tests/buffer_vdi_contract.cpp', 'buffer_vdi_contract')
    subprocess.run(['python3', str(ROOT / 'tools/project_vdi_headers.py')], check=True)
    import re
    source = (ROOT / 'adapter/composer_vdi.cpp').read_text()
    implemented = set(re.findall(r'extern "C" int32_t (\w+)\(', source))
    implemented.update(re.findall(r'SETTER\((\w+),', source))
    header = (ROOT / 'generated/vdi-only/composer_exports.h').read_text()
    methods = re.findall(r'extern "C" int32_t (\w+)\((.*?)\);', header, re.S)
    unsupported = '#include "composer_exports.h"\nnamespace OHOS::HDI::Display::Composer {\n'
    for name,args in methods:
        if name not in implemented:
            unsupported += f'extern "C" int32_t {name}({args}) {{ return -5; }}\n'
    unsupported += '}\n'
    unsupported_path = ROOT / 'generated/vdi-only/composer_unsupported.cpp'
    unsupported_path.write_text(unsupported)
    build('adapter/composer_vdi.cpp', 'libdisplay_composer_vdi_impl.z.so', True,
        [str(unsupported_path), str(STAGE/'lib/libdrm.a')])
    build('tests/composer_vdi_contract.cpp', 'composer_vdi_contract')
