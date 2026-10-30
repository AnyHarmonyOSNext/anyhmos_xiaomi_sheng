"""WSL: compile a bounded, read-only probe using original Wi-Fi C headers."""
from pathlib import Path
import hashlib, json, subprocess

r = Path(__file__).resolve().parent.parent
sdk = Path('/root/hmos-work/sdk-6.0.0.47/installed/native')
ref = Path('/root/hmos-work/graphics-deps/source/communication_wifi')
revision = subprocess.check_output(['git', '-C', str(ref), 'rev-parse', 'HEAD'], text=True).strip()
assert revision == 'abbb443cdd943a393b3d0b95d21df67262b7610e'
out = r / 'compat/debug-tools/native_wifi_link_v133'
subprocess.run([str(sdk/'llvm/bin/clang'), '--target=aarch64-linux-ohos', '-std=c11',
    '-Os', '-Wall', '-Wextra', '-Werror', '-I'+str(ref/'wifi/interfaces/kits/c'),
    str(r/'tools/native_wifi_link_v133.c'), '-ldl', '-o', str(out)], check=True)
subprocess.run([str(sdk/'llvm/bin/llvm-strip'), str(out)], check=True)
report = dict(source_revision=revision, read_only=True, bytes=out.stat().st_size,
    sha256=hashlib.sha256(out.read_bytes()).hexdigest(), native_link_result_verified=False)
(r/'analysis/wifi-link-probe-v133.json').write_text(json.dumps(report, indent=2)+'\n')
print(json.dumps(report))
