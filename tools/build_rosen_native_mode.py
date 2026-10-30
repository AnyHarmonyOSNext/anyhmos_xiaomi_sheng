"""Use original property-selected API, without changing DSO mode globals."""
from pathlib import Path
import json,subprocess,hashlib
base=Path('/root/hmos-work/graphics-deps');root=Path('/mnt/c/SHENG_WORKSPACE')
sdk=Path(json.loads(Path('/root/hmos-work/sdk-6.0.0.47/installation.json').read_text())['sdk'])
src=Path('/root/hmos-reference/AnyHarmonyOS/sm8650/graphics-port/gpu-port/src/rosen_gpu_contract.cpp').read_text()
old='printf("MODE_FIXTURE original_drawing=%d original_rs=%d selected_vulkan=1\\n",*drawingMode,*rsMode);*drawingMode=1;*rsMode=1;'
assert old in src
src=src.replace(old,'printf("NATIVE_MODE drawing=%d rs=%d global_override=0\\n",*drawingMode,*rsMode);CHECK(*drawingMode==1&&*rsMode==1);')
dest=root/'compat/sheng-graphics/rosen-native-mode-v1';dest.mkdir(exist_ok=True)
(dest/'rosen_native_mode.cpp').write_text(src)
cmd=[str(sdk/'llvm/bin/clang++'),'--target=aarch64-linux-ohos','-std=c++17','-O2','-fno-exceptions','-fno-rtti','-nostdlib++','-include',str(base/'sheng-graphics-port/tests/platform_cpp_config.h'),str(dest/'rosen_native_mode.cpp'),str(root/'work/donor-hdi-link/libc++.so'),'-o',str(dest/'rosen_native_mode')]
subprocess.run(cmd,check=True);subprocess.run([str(sdk/'llvm/bin/llvm-strip'),str(dest/'rosen_native_mode')],check=True)
b=(dest/'rosen_native_mode').read_bytes();report={'source_reference':'AnyHarmonyOS cb1ce16 rosen_gpu_contract.cpp','changes':'remove DSO GPU-mode assignments, assert native property-selected mode','bytes':len(b),'sha256':hashlib.sha256(b).hexdigest(),'command':cmd}
(root/'analysis/rosen-native-mode-build.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({k:v for k,v in report.items() if k!='command'},indent=2))
