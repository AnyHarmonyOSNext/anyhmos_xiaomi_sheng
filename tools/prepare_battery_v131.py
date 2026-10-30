"""Read donor battery HDI and generate the matching official API headers."""
from pathlib import Path
import hashlib
import json
import subprocess
import sys

r = Path(__file__).resolve().parent.parent
if sys.platform == 'win32':
    base = Path('C:/MIO-KITCHEN-PYSIDE6-5.0.0-PREVIEW')
    out = r / 'work/donor-battery-hdi'
    out.mkdir(exist_ok=True)
    report = []
    for name in ['libbattery_driver.z.so', 'libbattery_interface_service_2.0.z.so',
                 'libbattery_stub_2.0.z.so']:
        path = '/lib64/' + name
        target = out / 'vendor' / path.lstrip('/')
        if not target.exists():
            subprocess.run([str(base/'bin/Windows/AMD64/extract.erofs.exe'),
                            '-i', str(base/'hmos/vendor.img'), '-X', path,
                            '-o', str(out), '-s'], check=True, capture_output=True)
        data = target.read_bytes()
        assert data[:6] == b'\x7fELF\x02\x01'
        report.append(dict(path=path, bytes=len(data), sha256=hashlib.sha256(data).hexdigest()))
    (r/'analysis/battery-donor-inputs-v131.json').write_text(json.dumps(report, indent=2)+'\n')
    print(json.dumps(report, indent=2))
else:
    b = Path('/root/hmos-work/graphics-deps')
    s = b/'source/drivers_interface'
    out = b/'battery-hdi-generated'
    for path in sorted((s/'battery/v2_0').glob('*.idl')):
        subprocess.run([str(b/'hdi-gen'), '-s', 'full', '-m', 'ipc', '-l', 'cpp',
                        '-r', f'ohos.hdi:{s}', '-c', str(path), '-d', str(out)],
                       check=True, stdout=subprocess.DEVNULL)
    print('Battery headers:', len(list(out.rglob('*.h'))))
