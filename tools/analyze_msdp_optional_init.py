"""Locate donor MSDP optional distributed startup using its actual ELF bytes."""
from pathlib import Path
import sys
sys.path.insert(0, '/root/hmos-work/analysis-deps')
from capstone import Cs, CS_ARCH_ARM64, CS_MODE_LITTLE_ENDIAN
from elftools.elf.elffile import ELFFile

r = Path('/mnt/c/SHENG_WORKSPACE')
p = r / 'work/msdp-v116-original/libdevicestatus_service.z.so'
b = p.read_bytes()
with p.open('rb') as f:
    elf = ELFFile(f)
    loads = [s for s in elf.iter_segments() if s['p_type'] == 'PT_LOAD']
    sec = elf.get_section_by_name('.text')
    md = Cs(CS_ARCH_ARM64, CS_MODE_LITTLE_ENDIAN)
    instructions = list(md.disasm(sec.data(), sec['sh_addr']))
    names = sys.argv[1:] or ['EnableDDM', 'EnableDSoftbus', 'Failed to enable DistributedDeviceManager',
                            'Failed to enable dsoftbus']
    targets = {}
    for name in names:
        if name.startswith('@0x'):
            targets[int(name[1:], 16)] = name
            continue
        start = 0
        while (off := b.find(name.encode(), start)) >= 0:
            start = off + 1
            seg = next((s for s in loads if s['p_offset'] <= off < s['p_offset'] + s['p_filesz']), None)
            if seg is None:
                continue
            va = off - seg['p_offset'] + seg['p_vaddr']
            targets[va] = name
            print(f'STRING {name!r} file=0x{off:x} va=0x{va:x}')
    bases = {}
    for i, ins in enumerate(instructions):
        parts = ins.op_str.split(', ')
        target = None
        if ins.mnemonic in ('adrp', 'adr'):
            bases[parts[0]] = int(parts[1].lstrip('#'), 0)
            if ins.mnemonic == 'adr':
                target = bases[parts[0]]
        elif ins.mnemonic == 'add' and len(parts) == 3 and parts[1] in bases and parts[2].startswith('#'):
            target = bases[parts[1]] + int(parts[2][1:], 0)
        elif ins.mnemonic in ('bl', 'b') and parts[0].startswith('#'):
            target = int(parts[0][1:], 0)
        if target in targets:
            print('\nXREF', targets[target])
            for line in instructions[max(0, i-8):i+14]:
                print(f'{line.address:08x}: {line.mnemonic:8} {line.op_str}')
