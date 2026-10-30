#!/usr/bin/env python3
"""Project official generated types to the C-export VDI surface, no IPC ABI stubs.

Only the unused HdifdInfo parcel wrapper is removed; every VDI value type stays
byte-for-byte identical. The official generated directory remains unchanged.
"""
from pathlib import Path
import re, os
ROOT = Path(__file__).resolve().parents[1]
SOURCE = Path(os.environ['ANYHARMONYOS_OHOS_SOURCE'])
out = ROOT / 'generated/vdi-only'
for path in (ROOT / 'generated/display/composer').glob('v*/*.h'):
    if path.name.startswith('._'): continue
    s = path.read_text()
    if path.parent.name == 'v1_0':
        assert s.count('#include "hdifd_parcelable.h"') == 1
        s = s.replace('#include "hdifd_parcelable.h"', '')
        s, n = re.subn(r'struct HdifdInfo \{\n.*?\n\};\n', '', s, flags=re.S)
        assert n == 1
    s = s.replace('#include "hdifd_parcelable.h"', '')
    dest = out / path.relative_to(ROOT / 'generated')
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(s)
header = (SOURCE / 'drivers_interface/display/composer/common/include/display_vdi_adapter_interface.h').read_text()
methods = re.findall(r'int32_t \(\*(\w+)\)\((.*?)\);', header, flags=re.S)
assert len(methods) > 60
declarations = '\n'.join('extern "C" int32_t '+name+'('+args+');' for name,args in methods)
(out / 'composer_exports.h').write_text('''// Function signatures projected verbatim from the official VDI adapter.
#pragma once
#include "buffer_handle.h"
#include "display/composer/v1_3/display_composer_type.h"
#include "display_common.h"
namespace OHOS::HDI::Display::Composer {
using namespace OHOS::HDI::Display;
using namespace V1_0;
using namespace V1_1;
using namespace V1_2;
using namespace V1_3;
''' + declarations + '\n}\n')
