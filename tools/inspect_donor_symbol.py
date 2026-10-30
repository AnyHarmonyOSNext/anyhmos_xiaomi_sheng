"""Read an AArch64 donor symbol/instruction range through ELF PT_LOAD mappings."""
from pathlib import Path
import sys
sys.path.insert(0, '/root/hmos-work/analysis-deps')
from capstone import Cs, CS_ARCH_ARM64, CS_MODE_LITTLE_ENDIAN
from elftools.elf.elffile import ELFFile

p = Path(sys.argv[1])
with p.open('rb') as f:
    elf = ELFFile(f)
    spec = sys.argv[2]
    if spec.startswith('0x'):
        va, size = int(spec, 0), int(sys.argv[3], 0)
    else:
        syms = elf.get_section_by_name('.dynsym')
        sym = next(x for x in syms.iter_symbols() if x.name == spec)
        va, size = sym['st_value'], sym['st_size']
    seg = next(s for s in elf.iter_segments() if s['p_type'] == 'PT_LOAD' and s['p_vaddr'] <= va < s['p_vaddr'] + s['p_filesz'])
    assert seg['p_flags'] & 1
    f.seek(seg['p_offset'] + va - seg['p_vaddr'])
    data = f.read(size)
    for i in Cs(CS_ARCH_ARM64, CS_MODE_LITTLE_ENDIAN).disasm(data, va):
        print(f'{i.address:08x}: {i.bytes.hex()} {i.mnemonic:9} {i.op_str}')
