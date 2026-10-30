"""Locate the donor's native MemMgr init failure paths without guessed offsets."""
from pathlib import Path
import sys
sys.path.insert(0, '/root/hmos-work/analysis-deps')
from capstone import Cs, CS_ARCH_ARM64, CS_MODE_LITTLE_ENDIAN
from elftools.elf.elffile import ELFFile

r = Path('/mnt/c/SHENG_WORKSPACE')
p = r / 'work/hmos_system/system/system/lib64/libmemmgrservice.z.so'
b = p.read_bytes()
with p.open('rb') as f:
    elf = ELFFile(f)
    loads = [s for s in elf.iter_segments() if s['p_type'] == 'PT_LOAD']
    section = elf.get_section_by_name('.text')
    md = Cs(CS_ARCH_ARM64, CS_MODE_LITTLE_ENDIAN)
    instructions = list(md.disasm(section.data(), section['sh_addr']))
    names = [x.encode() for x in sys.argv[1:]] if len(sys.argv) > 1 else [b'%{public}s ReclaimStrategyManager init failed',
             b'%{public}s MemMgrEventCenter init failed',
             b'%{public}s ReclaimPriorityManager init failed',
             b'%{public}s publish SA successed']
    targets = {}
    for name in names:
        if name.startswith(b'@0x'):
            targets[int(name[1:], 16)] = name.decode()
            continue
        off = b.index(name)
        seg = next(s for s in loads if s['p_offset'] <= off < s['p_offset'] + s['p_filesz'])
        va = off - seg['p_offset'] + seg['p_vaddr']
        targets[va] = name.decode()
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
            for line in instructions[max(i-7, 0):i+9]:
                print(f'{line.address:08x}: {line.mnemonic:8} {line.op_str}')
