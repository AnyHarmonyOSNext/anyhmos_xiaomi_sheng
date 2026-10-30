from pathlib import Path
import hashlib
import json
import subprocess

root = Path(__file__).resolve().parent.parent
stock = Path('E:/SHENG_STOCK_303/images')
magisk = 'C:/MIO-KITCHEN-PYSIDE6-5.0.0-PREVIEW/bin/Windows/AMD64/magiskboot.exe'
build = root / 'work/probe_build_v51'
build.mkdir(exist_ok=True)
shell = 'cd "/mnt/c/SHENG_WORKSPACE" && aarch64-linux-gnu-gcc -static -O2 -Wall -Wextra -Werror tools/drm_probe.c -o compat/debug-tools/drm-probe-aarch64 && aarch64-linux-gnu-strip compat/debug-tools/drm-probe-aarch64'
subprocess.run(['wsl', '-d', 'Ubuntu-22.04', '--', 'bash', '-lc', shell], check=True)

for mode in ['probe', 'trace']:
    define = '-DTRACE_ANDROID' if mode == 'trace' else ''
    shell = f'cd "/mnt/c/SHENG_WORKSPACE" && aarch64-linux-gnu-gcc {define} -static -O2 -Wall -Wextra -Werror -o work/hmos_{mode}_v51 tools/hmos_probe.c && aarch64-linux-gnu-strip work/hmos_{mode}_v51'
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
            data = (root / f'work/hmos_{mode}_v51').read_bytes()
        entries.append((name, vals, data))
    config = (root / 'tools/configs/init-core-v51.cfg').read_bytes()
    json.loads(config)
    entries.append(('hmos-init-debug.cfg', [0,0o100644,0,0,1,0,0,0,0,0,0,0,0], config))
    entries.append(('hmos-ipc.ko', [0,0o100600,0,0,1,0,0,0,0,0,0,0,0], (root/'compat/sheng-hmos-ipc/v16/sheng_hmos_ipc.ko').read_bytes()))
    for test in ['token_contract','binder_nested']:
        entries.append((test,[0,0o100700,0,0,1,0,0,0,0,0,0,0,0],(root/'compat/sheng-hmos-ipc/tests'/test).read_bytes()))
    entries.append(('busybox',[0,0o100755,0,0,1,0,0,0,0,0,0,0,0],(root/'compat/debug-tools/busybox-aarch64').read_bytes()))
    entries.append(('drm-probe',[0,0o100755,0,0,1,0,0,0,0,0,0,0,0],(root/'compat/debug-tools/drm-probe-aarch64').read_bytes()))
    entries.append(('hmos-native-hilog',[0,0o100600,0,0,1,0,0,0,0,0,0,0,0],b'Native hilogd owns log sockets.\n'))
    entries.append(('graphics',[0,0o40755,0,0,2,0,0,0,0,0,0,0,0],b''))
    for file in sorted((root/'compat/sheng-graphics/v51').iterdir()):
        if file.is_file():entries.append(('graphics/'+file.name,[0,0o100755,0,0,1,0,0,0,0,0,0,0,0],file.read_bytes()))
    entries.append(('stock-gpu-firmware',[0,0o40755,0,0,2,0,0,0,0,0,0,0,0],b''))
    entries.append(('stock-gpu-firmware/a740_zap.mbn',[0,0o100644,0,0,1,0,0,0,0,0,0,0,0],(root/'work/stock_odm_runtime/odm/firmware/a740_zap.mbn').read_bytes()))
    entries.append(('hmos-hdf-graphics.hcb',[0,0o100644,0,0,1,0,0,0,0,0,0,0,0],(root/'compat/sheng-graphics/v51/hdf_default.hcb').read_bytes()))
    for file in sorted((root/'work/stock_vendor_runtime/vendor/firmware').iterdir()):
        if file.name.startswith('a740_') or file.name=='gmu_gen70200.bin':
            entries.append(('stock-gpu-firmware/'+file.name,[0,0o100644,0,0,1,0,0,0,0,0,0,0,0],file.read_bytes()))
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
    subprocess.run([magisk, 'repack', str(stock / 'init_boot.img'), str(root / f'output/init_boot_hmos_{mode}_v51.img')], cwd=build, check=True)

paths = [root / f'output/init_boot_hmos_{mode}_v51.img' for mode in ['probe','trace']]
paths += [root / 'tools/hmos_probe.c', root / 'tools/build_probe_v51.py']
paths += [root / 'tools/configs/init-core-v51.cfg']
paths += [root / 'compat/sheng-hmos-ipc/v16/sheng_hmos_ipc.ko']
paths += [root / 'compat/sheng-hmos-ipc/tests'/test for test in ['token_contract','binder_nested']]
paths += [root / 'tools/probe_command.inc',root/'compat/debug-tools/busybox-aarch64']
paths += [root/'tools/drm_probe.c',root/'compat/debug-tools/drm-probe-aarch64']
paths += [p for p in (root/'compat/sheng-graphics/v51').iterdir() if p.is_file()]
paths += [p for p in (root/'work/stock_vendor_runtime/vendor/firmware').iterdir() if p.name.startswith('a740_') or p.name=='gmu_gen70200.bin']
paths += [root/'tools/probe_graphics.inc',root/'tools/configs/sheng-graphics.hcs',root/'work/stock_odm_runtime/odm/firmware/a740_zap.mbn']
manifest = {}
for p in paths:
    with p.open('rb') as f:
        digest = hashlib.file_digest(f, 'sha256').hexdigest()
    manifest[str(p.relative_to(root))] = {'Bytes': p.stat().st_size, 'Sha256': digest}
(root / 'output/v51-manifest.json').write_text(json.dumps(manifest, indent=2), encoding='utf-8')


















