"""One-shot original DMS off/on recovery under the existing init identity."""
from pathlib import Path
import subprocess, json, hashlib
r=Path('/mnt/c/SHENG_WORKSPACE')
sdk=Path('/root/hmos-work/sdk-6.0.0.47/installed/native')
out=r/'compat/sheng-power/screen-v145';out.mkdir(exist_ok=True)
s=(r/'tools/native_display_wake_v2.cpp').read_text()
mark='    bool b = begin(d, 0);'
assert s.count(mark)==1
s=s.replace(mark,'''    // Test recovery only: original SCREEN_POWER_OFF=3 clears the stale FSM.
    bool off = power(s, 3, 0);
    printf("DMS_RECOVERY_POWER_OFF=%d\\n", off);
    if (!off) return 11;
    usleep(500000);
'''+mark)
src=out/'native_display_recover_v145.cpp';src.write_text(s)
exe=out/'native_display_recover_v145'
subprocess.run([str(sdk/'llvm/bin/clang++'),'--target=aarch64-linux-ohos','-Os','-Wall','-Wextra','-Werror','-std=c++17','-fno-exceptions','-fno-rtti','-nostdlib++','-include','/root/hmos-work/graphics-deps/sheng-graphics-port/tests/platform_cpp_config.h',str(src),str(r/'work/hmos_system/system/system/lib64/chipset-sdk-sp/libc++.so'),'-o',str(exe)],check=True)
subprocess.run([str(sdk/'llvm/bin/llvm-strip'),str(exe)],check=True)
print(json.dumps(dict(bytes=exe.stat().st_size,sha256=hashlib.sha256(exe.read_bytes()).hexdigest())))
