"""Check stock touch imports against rebuilt GKI and original vendor exports.

Package exact original modules and firmware for /compat; never patch module
metadata or disable the kernel's module version/CFI checks.
"""
from pathlib import Path
import hashlib, io, json, struct, subprocess, tarfile

r = Path(__file__).resolve().parents[1]

def sections(b):
    assert b[:6] == b'\x7fELF\x02\x01'
    off = struct.unpack_from('<Q', b, 40)[0]
    size, count, index = struct.unpack_from('<HHH', b, 58)
    table = [struct.unpack_from('<IIQQQQIIQQ', b, off + i * size) for i in range(count)]
    item = table[index]
    names = b[item[4]:item[4] + item[5]]
    return table, {names[s[0]:].split(b'\0', 1)[0].decode(): s for s in table}

def exports(b):
    table, named = sections(b)
    syms = named.get('.symtab')
    if not syms:
        return {}
    st = table[syms[6]]
    strings = b[st[4]:st[4] + st[5]]
    out = {}
    for pos in range(syms[4], syms[4] + syms[5], syms[9]):
        name, _, _, index, value, _ = struct.unpack_from('<IBBHQQ', b, pos)
        symbol = strings[name:].split(b'\0', 1)[0].decode()
        if symbol.startswith('__crc_') and index == 0xfff1:
            out[symbol[6:]] = value
    return out

symvers = subprocess.check_output(['wsl', '-d', 'Ubuntu-22.04', '--', 'cat',
    '/root/hmos-work/gki-out-sheng-exports/vmlinux.symvers'], text=True)
known = {v[1]: int(v[0], 16) for line in symvers.splitlines() if len(v := line.split()) >= 2}
cpio = (r / 'work/stock_vendor_boot/fragment_0_.lz4.cpio').read_bytes()
pos = 0
while pos + 110 <= len(cpio) and cpio[pos:pos + 6] == b'070701':
    v = [int(cpio[pos + 6 + j * 8:pos + 14 + j * 8], 16) for j in range(13)]
    name = cpio[pos + 110:pos + 110 + v[11] - 1].decode()
    off = (pos + 110 + v[11] + 3) & ~3
    b = cpio[off:off + v[6]]
    pos = (off + v[6] + 3) & ~3
    if name == 'TRAILER!!!':
        break
    if name.endswith('.ko'):
        for symbol, crc in exports(b).items():
            assert symbol not in known or known[symbol] == crc, (name, symbol)
            known[symbol] = crc

d = r / 'compat/sheng-touch/v1'
d.mkdir(parents=True, exist_ok=True)
sources = [(r / 'work/official303_vendor_dlkm/vendor_dlkm/lib/modules' / (n + '.ko'),
            'modules/' + n + '.ko') for n in ['xiaomi_touch', 'nt36532_touch']]
for p, _ in sources:
    known.update(exports(p.read_bytes()))
report = {'module_load_flags': 0, 'original_metadata_preserved': True, 'artifacts': {}}
payloads = []
for p, destination in sources:
    b = p.read_bytes()
    _, named = sections(b)
    s = named['__versions']
    data = b[s[4]:s[4] + s[5]]
    imports = {data[i + 8:i + 64].split(b'\0', 1)[0].decode():
        struct.unpack_from('<Q', data, i)[0] for i in range(0, len(data), 64)}
    bad = {n: (c, known.get(n)) for n, c in imports.items() if known.get(n) != c}
    assert not bad, (p.name, bad)
    assert imports['module_layout'] == 0x0222dd63 and b'__cfi_check\0' in b
    report['artifacts'][destination] = {'sha256': hashlib.sha256(b).hexdigest(),
        'bytes': len(b), 'imports_checked': len(imports), 'cfi_present': True}
    payloads.append((destination, b))

for name in ['novatek_nt36532_n81a_fw_csot.bin', 'novatek_nt36532_n81a_mp_csot.bin']:
    p = r / 'work/stock_touch_runtime/odm/firmware' / name
    b = p.read_bytes()
    destination = 'firmware/' + name
    report['artifacts'][destination] = {'sha256': hashlib.sha256(b).hexdigest(), 'bytes': len(b)}
    payloads.append((destination, b))

with tarfile.open(d / 'touch-bundle.tar.gz', 'w:gz') as tar:
    for name, b in payloads:
        info = tarfile.TarInfo(name)
        info.size, info.mode, info.mtime = len(b), 0o644, 0
        tar.addfile(info, io.BytesIO(b))
(d / 'manifest.json').write_text(json.dumps(report, indent=2) + '\n')
(r / 'analysis/touch-module-abi-verification.json').write_text(json.dumps(report, indent=2) + '\n')
print(json.dumps(report, indent=2))
print('bundle_bytes=', (d / 'touch-bundle.tar.gz').stat().st_size)
