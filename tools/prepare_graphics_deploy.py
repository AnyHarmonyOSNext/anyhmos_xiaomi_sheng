"""Keep debug binaries and create smaller RAM deployment copies."""
from pathlib import Path
import hashlib
import json
import subprocess
import re
import sys

workspace = Path('/mnt/c/SHENG_WORKSPACE')
label = sys.argv[1] if len(sys.argv) > 1 else 'v33'
assert re.fullmatch(r'v[0-9]+', label)
source = workspace / ('compat/sheng-graphics/' + label)
destination = workspace / ('compat/sheng-graphics/deploy-' + label)
destination.mkdir(exist_ok=True)
results = []
for name in ['libdisplay_composer_vdi_impl.z.so', 'sheng_display_scanout']:
    subprocess.run(['aarch64-linux-gnu-objcopy', '--strip-debug', str(source / name), str(destination / name)], check=True)
    data = (destination / name).read_bytes()
    results.append({'name': name, 'bytes': len(data), 'sha256': hashlib.sha256(data).hexdigest()})
(workspace / ('analysis/graphics-deploy-' + label + '.json')).write_text(json.dumps(results, indent=2) + '\n')
print(json.dumps(results, indent=2))
