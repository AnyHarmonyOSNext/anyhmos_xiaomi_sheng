from pathlib import Path
import subprocess
r=Path(__file__).resolve().parent.parent
sdk=Path('/root/hmos-work/sdk-6.0.0.47/installed/native/llvm/bin')
flags=['--target=aarch64-linux-ohos','-O2','-Wall','-Wextra','-Werror']
obj=r/'output/bt-current-v139.o'
subprocess.run([str(sdk/'clang'),*flags,'-DSHENG_CURRENT_BT_API','-c',str(r/'tools/native_bt_host_check_v137.c'),'-o',str(obj)],check=True)
out=r/'output/native_bt_host_check_v139'
subprocess.run([str(sdk/'clang++'),*flags,'-std=c++17','-nostdlib++','-fno-exceptions','-fno-rtti',
    '-include','/root/hmos-work/graphics-deps/sheng-graphics-port/tests/platform_cpp_config.h',
    str(r/'tools/native_bt_current_v139.cpp'),str(obj),str(r/'work/donor-hdi-link/libc++.so'),'-ldl','-Wl,--allow-shlib-undefined','-o',str(out)],check=True)
subprocess.run([str(sdk/'llvm-strip'),str(out)],check=True)
print(out.stat().st_size)
