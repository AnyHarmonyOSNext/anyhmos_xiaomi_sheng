"""Read donor audio ELFs for ABI inspection; never modify source images."""
from pathlib import Path
import hashlib
import json
import subprocess

r = Path(__file__).resolve().parent.parent
base = Path('C:/MIO-KITCHEN-PYSIDE6-5.0.0-PREVIEW')
exe = base/'bin/Windows/AMD64/extract.erofs.exe'
inputs = {
    'vendor': [
        '/lib64/libaudio_manager_service_6.1.z.so',
        '/lib64/libaudio_primary_driver.z.so',
        '/lib64/libaudio_primary_impl.z.so',
        '/lib64/libaudio_primary_impl_vendor.z.so',
    ],
    'system': [
        '/system/lib64/chipset-sdk/libaudio_proxy_6.1.z.so',
        '/system/lib64/chipset-sdk/libaudio_proxy_6.0.z.so',
        '/system/lib64/platformsdk/libaudio_manager_client.z.so',
    ],
}
out = r/'work/donor-audio-hdi'
out.mkdir(exist_ok=True)
report = []
for part, paths in inputs.items():
    for path in paths:
        target = out/part/path.lstrip('/')
        if not target.is_file():
            subprocess.run([str(exe), '-i', str(base/'hmos'/(part+'.img')),
                            '-X', path, '-o', str(out), '-s'],
                           capture_output=True, check=True)
        b = target.read_bytes()
        assert b.startswith(b'\x7fELF\x02\x01'), target
        report.append(dict(partition=part, path=path, local=str(target.relative_to(r)),
                           bytes=len(b), sha256=hashlib.sha256(b).hexdigest()))
(r/'analysis/donor-audio-hdi-inputs.json').write_text(
    json.dumps(report, indent=2)+'\n', encoding='utf-8')
print(json.dumps(report, indent=2))
