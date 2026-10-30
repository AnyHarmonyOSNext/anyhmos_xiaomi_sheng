"""Build only a bounded diagnostic; does not edit the production payload."""
from pathlib import Path
import hashlib
import json
import subprocess

r = Path(__file__).resolve().parent.parent
llvm = Path('/root/hmos-work/sdk-6.0.0.47/installed/native/llvm/bin')
out = r / 'compat/debug-tools/native_image_decode_probe_v129'
subprocess.run([str(llvm / 'clang++'), '--target=aarch64-linux-ohos',
    '-std=gnu++17', '-nostdlib++', '-O2',
    str(r / 'tools/native_image_decode_probe_v129.cpp'), '-ldl', '-o', str(out)], check=True)
subprocess.run([str(llvm / 'llvm-strip'), str(out)], check=True)
print(json.dumps(dict(file=str(out), bytes=out.stat().st_size,
    sha256=hashlib.sha256(out.read_bytes()).hexdigest())))
