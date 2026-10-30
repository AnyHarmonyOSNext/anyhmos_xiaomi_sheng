from pathlib import Path
import hashlib
import json
import subprocess

root = Path(__file__).resolve().parent.parent
stock = Path('E:/SHENG_STOCK_303/images')
magisk = 'C:/MIO-KITCHEN-PYSIDE6-5.0.0-PREVIEW/bin/Windows/AMD64/magiskboot.exe'
build = root / 'work/probe_build_v4'
build.mkdir(exist_ok=True)

for mode in ['probe', 'trace']:
    define = '-DTRACE_ANDROID' if mode == 'trace' else ''
    shell = f'cd "/mnt/c/SHENG_WORKSPACE" && aarch64-linux-gnu-gcc {define} -static -O2 -Wall -Wextra -Werror -o work/hmos_{mode}_v4 tools/hmos_probe.c && aarch64-linux-gnu-strip work/hmos_{mode}_v4'
    subprocess.run(['wsl', '-d', 'Ubuntu-22.04', '--', 'bash', '-lc', shell], check=True)
    b = (root / 'work/stock_init_boot/ramdisk.cpio').read_bytes()
    out = bytearray()
    entries = []
    i = 0
    while i + 110 <= len(b) and b[i:i+6] == b'070701':
        vals = [int(b[i+6+j*8:i+14+j*8], 16) for j in range(13)]
        name = b[i+110:i+110+vals[11]-1].decode()
        offset = (i+110+vals[11]+3) & ~3
        data = b[offset:offset+vals[6]]
        i = (offset+vals[6]+3) & ~3
        if name == 'TRAILER!!!':
            break
        if name == 'init':
            entries.append(('init.android.original', vals.copy(), data))
            data = (root / f'work/hmos_{mode}_v4').read_bytes()
        entries.append((name, vals, data))
    entries.append(('TRAILER!!!', [0,0,0,0,1,0,0,0,0,0,0,0,0], b''))
    for name, vals, data in entries:
        vals = vals.copy()
        nb = name.encode() + b'\0'
        vals[6], vals[11], vals[12] = len(data), len(nb), 0
        out.extend(b'070701' + ''.join(f'{v:08x}' for v in vals).encode() + nb)
        out.extend(bytes((-len(out)) % 4))
        out.extend(data)
        out.extend(bytes((-len(out)) % 4))
    out.extend(bytes((-len(out)) % 512))
    (build / 'ramdisk.cpio').write_bytes(out)
    (build / 'header').write_bytes((root / 'work/stock_init_boot/header').read_bytes())
    subprocess.run([magisk, 'repack', str(stock / 'init_boot.img'), str(root / f'output/init_boot_hmos_{mode}_v4.img')], cwd=build, check=True)

paths = [root / f'output/init_boot_hmos_{mode}_v4.img' for mode in ['probe','trace']]
paths += [root / 'tools/hmos_probe.c', root / 'tools/build_probe_v4.py']
manifest = {}
for p in paths:
    with p.open('rb') as f:
        digest = hashlib.file_digest(f, 'sha256').hexdigest()
    manifest[str(p.relative_to(root))] = {'Bytes': p.stat().st_size, 'Sha256': digest}
(root / 'output/v4-manifest.json').write_text(json.dumps(manifest, indent=2), encoding='utf-8')
