"""Build bounded diagnostics against the donor ABI and original IPC headers."""
from pathlib import Path
import hashlib, json, subprocess
r = Path('/mnt/c/SHENG_WORKSPACE')
sdk = Path('/root/hmos-work/sdk-6.0.0.47/installed/native')
link = r / 'work/donor-hdi-link'
common = [str(sdk/'llvm/bin/clang++'), '--target=aarch64-linux-ohos', '-std=c++17',
          '-Os', '-Wall', '-Wextra', '-fno-exceptions', '-fno-rtti', '-nostdlib++',
          '-include', '/root/hmos-work/graphics-deps/sheng-graphics-port/tests/platform_cpp_config.h']
out = r / 'compat/debug-tools'
subprocess.run([str(sdk/'llvm/bin/clang'), '--target=aarch64-linux-ohos', '-Os',
                '-Wall', '-Wextra', '-Werror', str(r/'tools/native_thp_launcher.c'),
                '-o', str(out/'native_thp_launcher')], check=True)
subprocess.run(common + [str(r/'tools/native_image_source_probe.cpp'), str(link/'libc++.so'),
                         '-ldl', '-o', str(out/'native_image_source_probe')], check=True)
commands = json.loads(Path('/root/hmos-work/sheng-useriam-port/out/build-commands.json').read_text())
cmd = commands[-1]
flags = cmd[1:cmd.index('-shared')]
screen = Path('/root/hmos-work/desktop-debug/theme_screenlock_mgr')
flags += ['-I'+str(screen/'interfaces/inner_api/include'),
          '-I'+str(screen/'frameworks/native/include'), '-Wno-unused-parameter']
subprocess.run([str(sdk/'llvm/bin/clang++'), *flags, str(r/'tools/native_screenlock_request.cpp'),
                str(r/'work/hmos_system/system/system/lib64/platformsdk/libscreenlock_client.z.so'),
                str(link/'libipc_single.z.so'), str(link/'libutils.z.so'), str(link/'libc++.so'),
                '-Wl,--allow-shlib-undefined', '-o', str(out/'native_screenlock_request')], check=True)
for name in ['native_image_source_probe', 'native_screenlock_request', 'native_thp_launcher']:
    path = out/name
    subprocess.run([str(sdk/'llvm/bin/llvm-strip'), str(path)], check=True)
    print(json.dumps(dict(name=name, bytes=path.stat().st_size,
                          sha256=hashlib.sha256(path.read_bytes()).hexdigest())))
