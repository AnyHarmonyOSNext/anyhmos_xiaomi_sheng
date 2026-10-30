"""Validate an isolated diagnostic module against the running kernel's exports."""
from pathlib import Path
import hashlib
import json
import struct
import sys

root = Path(__file__).resolve().parents[1]
module = root / sys.argv[1]
report_path = root / sys.argv[2]
data = module.read_bytes()
assert data[:4] == b'\x7fELF' and struct.unpack_from('<H', data, 18)[0] == 183
offset = struct.unpack_from('<Q', data, 40)[0]
size, count, names_index = struct.unpack_from('<HHH', data, 58)
sections = [struct.unpack_from('<IIQQQQIIQQ', data, offset + i * size) for i in range(count)]
names_section = sections[names_index]
names = data[names_section[4]:names_section[4] + names_section[5]]
imports = {}
info = b''
for section in sections:
    name = names[section[0]:].split(b'\0', 1)[0]
    content = data[section[4]:section[4] + section[5]]
    assert name not in (b'.BTF', b'.BTF.ext')
    if name == b'__versions':
        assert len(content) % 64 == 0
        for i in range(0, len(content), 64):
            imports[content[i + 8:i + 64].split(b'\0', 1)[0].decode()] = struct.unpack_from('<Q', content, i)[0]
    if name == b'.modinfo':
        info = content
exports = {line.split()[1]: int(line.split()[0], 16)
           for line in Path('/root/hmos-work/gki-out-sheng-exports/vmlinux.symvers').read_text().splitlines() if line.strip()}
assert imports and all(exports.get(name) == crc for name, crc in imports.items())
assert imports['module_layout'] == 0x0222dd63
assert b'vermagic=5.15.178-android13-8-00021-g6f2f96be86b9-ab13729987 ' in info
assert b'__cfi_check\0' in data
report = {'artifact': str(module.relative_to(root)), 'sha256': hashlib.sha256(data).hexdigest(),
          'bytes': len(data), 'imports': {name: hex(crc) for name, crc in imports.items()},
          'all_import_crcs_match_running_kernel': True, 'legacy_cfi_present': True,
          'btf_removed': True, 'runtime_tested': False}
report_path.write_text(json.dumps(report, indent=2) + '\n')
print(json.dumps(report, indent=2))
