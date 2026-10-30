"""Extract imported symbol CRCs from the original vendor ramdisk, read-only."""
from pathlib import Path
import json
import struct

root = Path(__file__).resolve().parent.parent
data = (root / 'work/stock_vendor_boot/fragment_0_.lz4.cpio').read_bytes()
pos = 0
symbols, modules, conflicts = {}, {}, []
while pos + 110 <= len(data) and data[pos:pos+6] in (b'070701', b'070702'):
    fields = [int(data[pos+6+j*8:pos+14+j*8], 16) for j in range(13)]
    name = data[pos+110:pos+110+fields[11]-1].decode()
    offset = (pos+110+fields[11]+3) & ~3
    binary = data[offset:offset+fields[6]]
    pos = (offset+fields[6]+3) & ~3
    if name == 'TRAILER!!!':
        break
    if not name.endswith('.ko'):
        continue
    assert binary[:6] == b'\x7fELF\x02\x01', name
    shoff = struct.unpack_from('<Q', binary, 40)[0]
    shsize, shnum, shstr = struct.unpack_from('<HHH', binary, 58)
    sections = [struct.unpack_from('<IIQQQQIIQQ', binary, shoff+j*shsize) for j in range(shnum)]
    strings_sec = sections[shstr]
    strings = binary[strings_sec[4]:strings_sec[4]+strings_sec[5]]
    count = 0
    vermagic = ''
    for section in sections:
        secname = strings[section[0]:].split(b'\0', 1)[0]
        payload = binary[section[4]:section[4]+section[5]]
        if secname == b'.modinfo':
            vermagic = next((x.decode() for x in payload.split(b'\0') if x.startswith(b'vermagic=')), '')
        if secname == b'__versions':
            assert len(payload) % 64 == 0, name
            for p in range(0, len(payload), 64):
                crc = struct.unpack_from('<Q', payload, p)[0]
                symbol = payload[p+8:p+64].split(b'\0', 1)[0].decode()
                if symbol in symbols and symbols[symbol] != crc:
                    conflicts.append([name, symbol, symbols[symbol], crc])
                symbols[symbol] = crc
                count += 1
    modules[name] = {'imports': count, 'vermagic': vermagic}
assert not conflicts, conflicts
report = {'symbols': {key: f'0x{val:08x}' for key, val in sorted(symbols.items())}, 'modules': modules}
(root / 'analysis/stock-module-import-crcs.json').write_text(json.dumps(report, indent=2))
print(f'{len(modules)} modules, {len(symbols)} distinct symbol CRCs, no conflicts')
print('module_layout:', report['symbols'].get('module_layout'))
