"""Build with the actual donor platform libc++ and original public HDI ABI."""
from pathlib import Path
import subprocess,hashlib,json
r=Path(__file__).resolve().parent.parent
b=Path('/root/hmos-work/graphics-deps');s=b/'source'
sdk=Path('/root/hmos-work/sdk-6.0.0.47/installed/native')
incs=[b/'bluetooth-hdi-generated',b/'bluetooth-hdi-generated/bluetooth/hci',s/'drivers_hdf_core/interfaces/inner_api/hdi',
 s/'drivers_hdf_core/interfaces/inner_api/ipc',s/'drivers_hdf_core/interfaces/inner_api/hdi/base',
 s/'drivers_hdf_core/interfaces/inner_api/utils',s/'drivers_hdf_core/interfaces/inner_api/osal/uhdf',
 s/'drivers_hdf_core/interfaces/inner_api/core',s/'commonlibrary_c_utils/base/include',
 s/'communication_ipc/interfaces/innerkits/ipc_core/include',s/'communication_ipc/interfaces/innerkits/ipc_single/include',
 s/'hiviewdfx_hilog/interfaces/native/innerkits/include']
libs=r/'work/donor-hdi-link'
common=[str(sdk/'llvm/bin/clang++'),'--target=aarch64-linux-ohos','-std=c++17',
 '-O2','-Wall','-Wextra','-fno-exceptions','-fno-rtti','-nostdlib++',
 '-include',str(b/'sheng-graphics-port/tests/platform_cpp_config.h')]+['-I'+str(p) for p in incs]
for name in ('native_bt_hdi_check_v136','native_bt_hdi_publisher_v136'):
    out=r/'output'/name
    cmd=common+[str(r/f'tools/{name}.cpp')]
    cmd+=[str(libs/n) for n in ['libhdi.z.so','libhdi_base.z.so','libutils.z.so','libipc_single.z.so','libipc_common.z.so','libc++.so']]
    cmd+=[str(r/'work/donor-bluetooth-v136/vendor/lib64/libbluetooth_hci_stub_1.0.z.so')]
    cmd+=['-ldl','-Wl,--allow-shlib-undefined','-o',str(out)]
    subprocess.run(cmd,check=True)
    subprocess.run([str(sdk/'llvm/bin/llvm-strip'),str(out)],check=True)
    print(json.dumps(dict(file=out.name,bytes=out.stat().st_size,sha256=hashlib.sha256(out.read_bytes()).hexdigest())))
