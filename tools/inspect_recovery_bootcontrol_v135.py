"""Read only: inspect backed-up TWRP boot-control tools and their dependencies."""
from pathlib import Path
import subprocess
import json
from vendor_ramdisk_edit import parse, sha, MAGISKBOOT

r = Path(__file__).resolve().parent.parent
source = r / 'output/device-backup/YOUR_DEVICE_SERIAL/a/recovery_a.img'
out = r / 'work/recovery-bootcontrol-v135'
out.mkdir(exist_ok=True)
if not (out / 'ramdisk.cpio').exists():
    result = subprocess.run([MAGISKBOOT, 'unpack', str(source)], cwd=out,
                            check=True, capture_output=True)
    (out / 'unpack.txt').write_bytes(result.stdout + result.stderr)
entries = parse((out / 'ramdisk.cpio').read_bytes())
names = [n for n in entries if any(s in n.lower() for s in ['bootctl', 'bootcontrol', 'boot_control'])]
report = dict(source=str(source.relative_to(r)), sha256=sha(source.read_bytes()),
              tools=[dict(name=n, bytes=len(entries[n][1]), mode=oct(entries[n][0][1]),
                          sha256=sha(entries[n][1])) for n in names],
              library_names=[n for n in entries if n.endswith('.so') or n.endswith('linker64')])
for n in names:
    p = out / 'files' / n
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_bytes(entries[n][1])
(r / 'analysis/recovery-bootcontrol-v135-inspection.json').write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8')
print(json.dumps(dict(sha256=report['sha256'], tools=report['tools'], library_count=len(report['library_names'])), indent=2))
