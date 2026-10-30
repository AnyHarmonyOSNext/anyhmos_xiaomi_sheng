"""Build the read-only HDI client using official generated headers/donor ABI."""
from pathlib import Path
import json,subprocess,hashlib,sys
base=Path('/root/hmos-work/graphics-deps');source=base/'source'
workspace=Path('/mnt/c/SHENG_WORKSPACE')
sdk=Path(json.loads(Path('/root/hmos-work/sdk-6.0.0.47/installation.json').read_text())['sdk'])
include=[base/'hdi-generated',base/'hdi-generated/display/composer',
 source/'drivers_interface/display/composer',source/'drivers_interface/display/buffer',base/'hdi-generated/display/buffer',
 source/'drivers_hdf_core/interfaces/inner_api/ipc',base/'sheng-graphics-port/generated/display/buffer',
 source/'drivers_hdf_core/interfaces/inner_api/hdi',source/'drivers_hdf_core/interfaces/inner_api/hdi/base',source/'drivers_hdf_core/interfaces/inner_api/utils',
 source/'drivers_hdf_core/interfaces/inner_api/osal/uhdf',
 source/'drivers_interface/display/composer/hdifd_parcelable',
 source/'commonlibrary_c_utils/base/include',source/'communication_ipc/interfaces/innerkits/ipc_core/include',source/'communication_ipc/interfaces/innerkits/ipc_single/include',
 source/'hiviewdfx_hilog/interfaces/native/innerkits/include',source/'bounds_checking_function/include']
link=workspace/'work/donor-hdi-link'
client_source=workspace/(sys.argv[1] if len(sys.argv)>1 else 'tools/sheng_hdi_query.cpp')
out=workspace/(sys.argv[2] if len(sys.argv)>2 else 'compat/sheng-graphics/client-v1/sheng_hdi_query')
report_path=workspace/(sys.argv[3] if len(sys.argv)>3 else 'analysis/hdi-query-build.json')
out.parent.mkdir(parents=True,exist_ok=True)
command=[str(sdk/'llvm/bin/clang++'),'--target=aarch64-linux-ohos','-std=c++17','-O2','-fno-exceptions','-fno-rtti','-nostdlib++',
 '-include',str(base/'sheng-graphics-port/tests/platform_cpp_config.h')]
command += ['-I'+str(p) for p in include]
command += [str(client_source)]
command += [str(link/name) for name in ['libdisplay_composer_proxy_1.3.z.so','libutils.z.so','libhdi.z.so','libhdi_base.z.so','libipc_single.z.so','libipc_common.z.so','libhdf_utils.z.so','libc++.so']]
if client_source.name=='sheng_hdi_smq.cpp':
    command += [str(link/name) for name in ['libhilog.so','libsec_shared.z.so']]
if client_source.name=='sheng_hdi_scanout.cpp':
    command += [str(link/name) for name in ['libdisplay_composer_hdi_impl_1.3.z.so','libdisplay_buffer_hdi_impl.z.so']]
# All dependency payloads remain in the real device image. Only unresolved
# references *inside those input DSOs* are deferred to its runtime linker.
command += ['-Wl,--allow-shlib-undefined','-Wl,-rpath-link,'+str(link),'-o',str(out)]
result=subprocess.run(command,capture_output=True,text=True)
if result.returncode:
    print(result.stderr);sys.exit(result.returncode)
subprocess.run([str(sdk/'llvm/bin/llvm-strip'),str(out)],check=True)
report={'command':command,'bytes':out.stat().st_size,'sha256':hashlib.sha256(out.read_bytes()).hexdigest(),'readelf':subprocess.check_output([str(sdk/'llvm/bin/llvm-readelf'),'-h','-d',str(out)],text=True)}
report_path.write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps({k:v for k,v in report.items() if k not in ['readelf','command']},indent=2))
