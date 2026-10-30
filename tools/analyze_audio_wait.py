"""Locate donor audio policy wait paths from actual strings, never shared offsets."""
from pathlib import Path
import sys
sys.path.insert(0,'/root/hmos-work/analysis-deps')
from capstone import Cs,CS_ARCH_ARM64,CS_MODE_LITTLE_ENDIAN
from elftools.elf.elffile import ELFFile
r=Path('/mnt/c/SHENG_WORKSPACE')
p=r/'work/hmos_system/system/system/lib64/libaudio_policy_service.z.so'
b=p.read_bytes()
with p.open('rb') as f:
    elf=ELFFile(f);loads=[s for s in elf.iter_segments() if s['p_type']=='PT_LOAD']
    targets={}
    for word in sys.argv[1:] or ['GetNetworkIdByGroupId: has no valid group','GetNetworkIdByGroupId','GetVolumeGroupInfos']:
        start=0
        while True:
            off=b.find(word.encode(),start)
            if off<0:break
            start=off+len(word)
            off=b.rfind(b'\0',0,off)+1
            seg=next(s for s in loads if s['p_offset']<=off<s['p_offset']+s['p_filesz'])
            va=off-seg['p_offset']+seg['p_vaddr'];targets[va]=word;print('STRING',word,hex(va))
    sec=elf.get_section_by_name('.text');md=Cs(CS_ARCH_ARM64,CS_MODE_LITTLE_ENDIAN);md.skipdata=True
    instructions=list(md.disasm(sec.data(),sec['sh_addr']));bases={}
    for i,ins in enumerate(instructions):
        parts=ins.op_str.split(', ');target=None
        if ins.mnemonic in ('adrp','adr'):
            bases[parts[0]]=int(parts[1].lstrip('#'),0)
            if ins.mnemonic=='adr':target=bases[parts[0]]
        elif ins.mnemonic=='add' and len(parts)==3 and parts[1] in bases and parts[2].startswith('#'):
            target=bases[parts[1]]+int(parts[2][1:],0)
        if target in targets:
            print('\nXREF',targets[target])
            for line in instructions[max(i-8,0):i+12]:print(f'{line.address:08x}: {line.mnemonic:8} {line.op_str}')
