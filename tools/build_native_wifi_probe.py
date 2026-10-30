from pathlib import Path
import json
import subprocess

r = Path(__file__).resolve().parent.parent
b = Path('/root/hmos-work/graphics-deps')
sdk = Path(json.loads(Path('/root/hmos-work/sdk-6.0.0.47/installation.json').read_text())['sdk'])
w = b / 'source/drivers_peripheral/wlan'
includes = [w / 'interfaces/include', w / 'client/include']
subprocess.run([str(sdk/'llvm/bin/clang'), '--target=aarch64-linux-ohos', '-std=c11',
                '-O2', '-Wall', '-Wextra', '-Werror',
                *['-I' + str(p) for p in includes],
                str(r/'tools/native_wifi_hal_probe.c'), '-ldl',
                '-o', str(r/'compat/debug-tools/native_wifi_hal_probe')], check=True)
subprocess.run([str(sdk/'llvm/bin/clang'), '--target=aarch64-linux-ohos', '-std=c11',
                '-O2', '-Wall', '-Wextra', '-Werror',
                '-I'+str(b/'wlan-hdi-generated'),
                '-I'+str(b/'source/drivers_hdf_core/interfaces/inner_api/utils'),
                '-I'+str(b/'source/drivers_hdf_core/interfaces/inner_api/osal/uhdf'),
                str(r/'tools/native_wlan_hdi_probe.c'), '-ldl',
                '-o', str(r/'compat/debug-tools/native_wlan_hdi_probe')], check=True)
