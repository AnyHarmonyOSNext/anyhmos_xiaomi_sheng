"""Read original303 file listings for the separate audio compatibility runtime."""
from pathlib import Path
import json
import re
import subprocess

r = Path(__file__).resolve().parent.parent
exe = 'C:/MIO-KITCHEN-PYSIDE6-5.0.0-PREVIEW/bin/Windows/AMD64/extract.erofs.exe'
base = Path('C:/MIO-KITCHEN-PYSIDE6-5.0.0-PREVIEW/303')
report = []
for part, directory in [('vendor', '/lib64'), ('vendor', '/bin'), ('vendor', '/etc'), ('vendor', '/firmware'), ('odm', '/firmware'), ('odm', '/etc')]:
    result = subprocess.run([exe, '-i', str(base / (part + '.img')), '-P', directory, '-s'], capture_output=True, check=True)
    listing = result.stdout.decode('utf-8', errors='replace')
    (r / 'analysis' / ('stock-audio-list-' + part + directory.replace('/', '-') + '.txt')).write_text(listing, encoding='utf-8')
    paths = []
    for line in listing.splitlines():
        match = re.search(r'type=(FILE|SYMLINK) .*fsConfig=\[(/[^ ]+)', line)
        if not match:
            continue
        p = match[2]
        if re.search(r'(?i)agm|ar-pal|ar-gsl|ar-osal|tinyalsa|audio|acdb|cs35|cirrus|spkr', p):
            paths.append(p)
    report.append(dict(partition=part, directory=directory, files=paths))
(r / 'analysis/stock-audio-runtime-files.json').write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8')
for record in report:
    print(record['partition'], record['directory'])
    for p in record['files']:
        print(' ', p)
