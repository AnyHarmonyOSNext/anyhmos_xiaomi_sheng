"""Build the read-only donor battery diagnostic with the matching platform ABI."""
from pathlib import Path
import hashlib, json, subprocess
r=Path(__file__).resolve().parent.parent
b=Path('/root/hmos-work/graphics-deps'); s=b/'source'
sdk=Path('/root/hmos-work/sdk-6.0.0.47/installed/native')
incs=[b/'battery-hdi-generated',
      s/'drivers_hdf_core/interfaces/inner_api/hdi',
      s/'drivers_hdf_core/interfaces/inner_api/ipc',
      s/'drivers_hdf_core/interfaces/inner_api/hdi/base',
      s/'drivers_hdf_core/interfaces/inner_api/utils',
      s/'drivers_hdf_core/interfaces/inner_api/osal/uhdf',
      s/'commonlibrary_c_utils/base/include',
      s/'communication_ipc/interfaces/innerkits/ipc_core/include',
      s/'communication_ipc/interfaces/innerkits/ipc_single/include',
      s/'hiviewdfx_hilog/interfaces/native/innerkits/include']
out=r/'compat/debug-tools/native_battery_probe_v131'
libs=r/'work/donor-hdi-link'
cmd=[str(sdk/'llvm/bin/clang++'),'--target=aarch64-linux-ohos','-std=c++17',
     '-O2','-Wall','-Wextra','-fno-exceptions','-fno-rtti','-nostdlib++',
     '-include',str(b/'sheng-graphics-port/tests/platform_cpp_config.h')]
cmd+=['-I'+str(p) for p in incs]
cmd+=[str(r/'tools/native_battery_probe_v131.cpp'),str(libs/'libutils.z.so'),str(libs/'libc++.so'),
      '-ldl','-o',str(out)]
subprocess.run(cmd,check=True)
subprocess.run([str(sdk/'llvm/bin/llvm-strip'),str(out)],check=True)
report=dict(bytes=out.stat().st_size,sha256=hashlib.sha256(out.read_bytes()).hexdigest())
(r/'analysis/battery-probe-build-v131.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps(report))
pub=r/'compat/debug-tools/native_battery_hdi_publisher_v131'
cmd=cmd[:cmd.index(str(r/'tools/native_battery_probe_v131.cpp'))]
cmd+=['-I'+str(s/'drivers_hdf_core/interfaces/inner_api/core'),
      str(r/'tools/native_battery_hdi_publisher_v131.cpp')]
cmd+=[str(libs/name) for name in ['libhdi.z.so','libhdi_base.z.so','libutils.z.so',
      'libipc_single.z.so','libipc_common.z.so','libc++.so']]
cmd+=['-ldl','-Wl,--allow-shlib-undefined','-o',str(pub)]
subprocess.run(cmd,check=True)
subprocess.run([str(sdk/'llvm/bin/llvm-strip'),str(pub)],check=True)
print(json.dumps(dict(publisher_bytes=pub.stat().st_size,
                     publisher_sha256=hashlib.sha256(pub.read_bytes()).hexdigest())))
capi=r/'compat/debug-tools/native_battery_capi_v131'
subprocess.run([str(sdk/'llvm/bin/clang'),'--target=aarch64-linux-ohos','-O2','-Wall','-Wextra',
    '-I'+str(s/'powermgr_battery_manager/interfaces/kits/c'),
    str(r/'tools/native_battery_capi_v131.c'),'-ldl','-o',str(capi)],check=True)
subprocess.run([str(sdk/'llvm/bin/llvm-strip'),str(capi)],check=True)
print(json.dumps(dict(capi_bytes=capi.stat().st_size,
                     capi_sha256=hashlib.sha256(capi.read_bytes()).hexdigest())))
