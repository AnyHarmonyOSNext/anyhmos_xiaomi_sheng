"""Build separately so the validated v78 artifacts remain unchanged."""
from pathlib import Path
import hashlib, json, subprocess
r = Path('/mnt/c/SHENG_WORKSPACE')
sdk = Path('/root/hmos-work/sdk-6.0.0.47/installed/native')
link = r/'work/donor-hdi-link'
commands = json.loads(Path('/root/hmos-work/sheng-useriam-port/out/build-commands.json').read_text())
cmd = commands[-1]
flags = cmd[1:cmd.index('-shared')]
screen = Path('/root/hmos-work/desktop-debug/theme_screenlock_mgr')
flags += ['-I'+str(screen/'interfaces/inner_api/include'), '-I'+str(screen/'frameworks/native/include'), '-Wno-unused-parameter']
out = r/'compat/debug-tools/native_screenlock_request_v3'
subprocess.run([str(sdk/'llvm/bin/clang++'), *flags, str(r/'tools/native_screenlock_request_v3.cpp'),
               str(r/'work/hmos_system/system/system/lib64/platformsdk/libscreenlock_client.z.so'),
               str(link/'libipc_single.z.so'), str(link/'libutils.z.so'), str(link/'libc++.so'),
               '-Wl,--allow-shlib-undefined', '-o', str(out)], check=True)
subprocess.run([str(sdk/'llvm/bin/llvm-strip'), str(out)], check=True)
print(json.dumps(dict(bytes=out.stat().st_size, sha256=hashlib.sha256(out.read_bytes()).hexdigest())))
