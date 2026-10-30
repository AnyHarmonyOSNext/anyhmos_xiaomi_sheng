from pathlib import Path
import json,subprocess,hashlib
root=Path('/mnt/c/SHENG_WORKSPACE');base=Path('/root/hmos-work/graphics-deps')
sdk=Path('/root/hmos-work/sdk-6.0.0.47/installed/native')
dest=root/'compat/sheng-graphics/bootanimation-vulkan-adapter-v1';dest.mkdir(exist_ok=True)
cmd=[str(sdk/'llvm/bin/clang++'),'--target=aarch64-linux-ohos','-shared','-fPIC','-std=c++17','-O2','-fno-exceptions','-fno-rtti','-nostdlib++','-include',str(base/'sheng-graphics-port/tests/platform_cpp_config.h'),str(root/'tools/bootanimation_vulkan_adapter.cpp'),str(root/'work/donor-hdi-link/libc++.so'),'-Wl,-z,defs','-o',str(dest/'libsheng_boot_vulkan.so')]
subprocess.run(cmd,check=True)
subprocess.run([str(sdk/'llvm/bin/clang'),'--target=aarch64-linux-ohos','-O2',str(root/'tools/bootanimation_native_launcher.c'),'-o',str(dest/'bootanimation-launcher')],check=True)
report={}
for name in ['libsheng_boot_vulkan.so','bootanimation-launcher']:
 p=dest/name;subprocess.run([str(sdk/'llvm/bin/llvm-strip'),str(p)],check=True)
 report[name]={'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()}
report.update(render_base_required_sha256='0a699e2317dab4699117a90e7e21d5727bd823e3474a70ebaed4d32667e519ff',
 status='candidate; not tested',source_basis='OpenHarmony-6.0-Release public inline RSSurfaceOhosVulkan::SetSkContext; exact donor layout verified in constructor and RequestFrame',context_member_offset=312)
(dest/'manifest.json').write_text(json.dumps(report,indent=2)+'\n')
(root/'analysis/bootanimation-vulkan-adapter-build.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps(report,indent=2))
