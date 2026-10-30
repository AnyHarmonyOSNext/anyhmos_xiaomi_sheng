"""Produce a bounded dependency-ordered loader for untouched official303 modules."""
from pathlib import Path
import hashlib
import json
import re
import struct
import sys

r = Path(__file__).resolve().parent.parent
modules = r / 'work/official303_vendor_dlkm/vendor_dlkm/lib/modules'
target = sys.argv[1]
assert re.fullmatch(r'[A-Za-z0-9_-]+', target)
deps = {}
for line in (modules / 'modules.dep').read_text().splitlines():
    key, values = line.split(':', 1)
    deps[Path(key).name] = [Path(v).name for v in values.split()]
order = []
visiting = set()

def visit(name):
    if name in order:
        return
    assert name not in visiting, f'Cycle: {name}'
    visiting.add(name)
    assert name in deps and (modules / name).is_file(), name
    for dep in deps[name]:
        visit(dep)
    visiting.remove(name)
    order.append(name)

visit(target + '.ko')

def elf(data):
    assert data[:6] == b'\x7fELF\x02\x01'
    offset = struct.unpack_from('<Q', data, 40)[0]
    size, count, strings_index = struct.unpack_from('<HHH', data, 58)
    table = [struct.unpack_from('<IIQQQQIIQQ', data, offset + i * size)
             for i in range(count)]
    section = table[strings_index]
    strings = data[section[4]:section[4] + section[5]]
    named = {strings[s[0]:].split(b'\0', 1)[0].decode(): s for s in table}
    return table, named

def exports(data):
    table, named = elf(data)
    symtab = named.get('.symtab')
    if not symtab:
        return {}
    names = table[symtab[6]]
    strings = data[names[4]:names[4] + names[5]]
    result = {}
    for offset in range(symtab[4], symtab[4] + symtab[5], symtab[9]):
        name, _, _, index, value, _ = struct.unpack_from('<IBBHQQ', data, offset)
        name = strings[name:].split(b'\0', 1)[0].decode()
        if index == 0xfff1 and name.startswith('__crc_'):
            result[name[6:]] = value
    return result

# The running ShengExports kernel has the exact original CRCs and additional
# exports. Original vendor-ramdisk modules are loaded before this plan.
known = {v[1]: int(v[0], 16) for line in
         (r / 'analysis/gki-sheng-exports.symvers').read_text().splitlines()
         if len(v := line.split()) >= 2}
cpio = (r / 'work/stock_vendor_boot/fragment_0_.lz4.cpio').read_bytes()
pos = 0
while pos + 110 <= len(cpio) and cpio[pos:pos + 6] in (b'070701', b'070702'):
    fields = [int(cpio[pos + 6 + i * 8:pos + 14 + i * 8], 16) for i in range(13)]
    name = cpio[pos + 110:pos + 110 + fields[11] - 1].decode()
    offset = (pos + 110 + fields[11] + 3) & ~3
    data = cpio[offset:offset + fields[6]]
    pos = (offset + fields[6] + 3) & ~3
    if name == 'TRAILER!!!':
        break
    if name.endswith('.ko'):
        for symbol, crc in exports(data).items():
            assert symbol not in known or known[symbol] == crc, (name, symbol)
            known[symbol] = crc

observed = json.loads((r / 'analysis/stock-module-import-crcs.json').read_text())['symbols']
entries = []
for name in order:
    data = (modules / name).read_bytes()
    _, named = elf(data)
    sec = named['.modinfo']
    info = dict(v.split('=', 1) for v in
                data[sec[4]:sec[4] + sec[5]].decode().split('\0') if '=' in v)
    # Exact kernel/module.c same_magic(has_crcs): release prefix is ignored,
    # while the suffix and all symbol CRCs remain mandatory. No force flags.
    assert info['vermagic'].partition(' ')[2] == 'SMP preempt mod_unload modversions aarch64', name
    sec = named['__versions']
    versions = data[sec[4]:sec[4] + sec[5]]
    assert versions and len(versions) % 64 == 0, name
    imports = {versions[i + 8:i + 64].split(b'\0', 1)[0].decode():
               struct.unpack_from('<Q', versions, i)[0] for i in range(0, len(versions), 64)}
    # Exports from the current module can satisfy its own import table too.
    own = exports(data)
    for symbol, crc in own.items():
        assert symbol not in known or known[symbol] == crc, (name, symbol)
    available = known | own
    bad = {s: [hex(c), hex(available[s]) if s in available else None]
           for s, c in imports.items() if available.get(s) != c}
    assert not bad, (name, bad)
    assert all(c == int(observed[s], 16) for s, c in imports.items() if s in observed), name
    assert imports['module_layout'] == 0x0222dd63 and b'__cfi_check\0' in data, name
    known.update(own)
    entries.append(dict(file=name, name=info['name'], bytes=len(data),
                        sha256=hashlib.sha256(data).hexdigest(), vermagic=info['vermagic'],
                        imports_checked=len(imports), cfi_present=True, module_load_flags=0))
script = ['#!/busybox sh', 'set -eu', 'B=/busybox', 'R=/hmos-root',
          'M=$R/vendor_dlkm/lib/modules',
          '''[ "$($B uname -r)" = 5.15.178-android13-8-00021-g6f2f96be86b9-ab13729987 ] || exit 30''',
          f'echo STOCK_MODULE_PLAN_BEGIN={target}']
for e in entries:
    script += [f"if $B grep -q '^{e['name']} ' /proc/modules; then",
               f" echo MODULE_ALREADY_PRESENT={e['name']}", 'else',
               f" echo '{e['sha256']}  '$M/{e['file']} | $B sha256sum -c -",
               f" echo MODULE_LOAD_BEGIN={e['file']}",
               f" $B timeout 12 $B insmod $M/{e['file']} || {{ code=$?; echo MODULE_LOAD_FAILED={e['file']}:$code; exit $code; }}",
               f" $B grep '^{e['name']} ' /proc/modules", 'fi']
script += [f'echo STOCK_MODULE_PLAN_COMPLETE={target}']
out = r / 'analysis' / f'official303-{target}-module-plan.json'
out.write_text(json.dumps(entries, indent=2) + '\n', encoding='utf-8')
out = r / 'output' / f'load-official303-{target}.sh'
out.write_text('\n'.join(script) + '\n', encoding='utf-8', newline='\n')
print(json.dumps(dict(target=target, count=len(entries), modules=[x['file'] for x in entries], script=str(out)), indent=2))
