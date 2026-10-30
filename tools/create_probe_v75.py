"""Stage bounded Vulkan native-buffer diagnostics without touching vendor."""
from pathlib import Path
import shutil, json

r = Path(__file__).resolve().parents[1]
d = r / 'compat/sheng-graphics/v75'
assert not d.exists(), 'Do not overwrite a staged version'
for name in ['hmos_probe.c', 'probe_graphics.inc', 'probe_command.inc']:
    p = r / 'tools' / name
    frozen = r / 'tools/archive' / (p.stem + '_v74' + p.suffix)
    assert not frozen.exists()
    shutil.copy2(p, frozen)
shutil.copytree(r / 'compat/sheng-graphics/v74', d)
diag = r / 'compat/sheng-graphics/gpu-diagnostic-v1'
manifest = json.loads((diag / 'manifest.json').read_text())
shutil.copy2(diag / 'libvulkan_freedreno.so.gz', d)
p = d / 'apply-compat-paths.sh'
p.write_text(p.read_text().replace('ce6413a25a0fb8cf3cf3d58a0026e506889ab171435b34eb2bc383e6d29503d9', manifest['sha256']), newline='\n')
p = r / 'tools/hmos_probe.c'
p.write_text(p.read_text().replace('v74', 'v75'))
shutil.copy2(r / 'tools/configs/init-core-v74.cfg', r / 'tools/configs/init-core-v75.cfg')
for name in ['build_probe', 'verify']:
    p = r / f'tools/{name}_v74.py'
    data = p.read_text().replace('v74', 'v75')
    if name == 'verify':
        data = data.replace("compat/sheng-graphics/gpu-v1/libvulkan_freedreno.so", "compat/sheng-graphics/gpu-diagnostic-v1/libvulkan_freedreno.so")
    (r / f'tools/{name}_v75.py').write_text(data)
print('v75 staged; native buffer diagnostics SHA256=' + manifest['sha256'])
