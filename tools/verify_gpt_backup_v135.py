"""Read-only CRC/primary-backup checks for bounded device GPT captures."""
from pathlib import Path
import json
import struct
import sys
import tarfile
import zlib

root=Path(__file__).resolve().parent.parent
archive=Path(sys.argv[1])
with tarfile.open(archive,'r:gz') as tar:
    entries={m.name.removeprefix('./'):tar.extractfile(m).read() for m in tar.getmembers() if m.isfile()}
report=dict(source=str(archive),boot_id=entries['boot-id.txt'].decode().strip(),disks={})
for row in entries['layout.txt'].decode().splitlines():
    disk,sectors,sector,blocks=row.split();sector=int(sector);blocks=int(blocks)
    head,tail=entries[disk+'-head.bin'],entries[disk+'-tail.bin']
    assert len(head)==sector*34 and len(tail)==sector*33
    def parse(blob,start,header_lba):
        pos=(header_lba-start)*sector; h=blob[pos:pos+sector]
        assert h[:8]==b'EFI PART',(disk,header_lba,'signature')
        hs,hc=struct.unpack_from('<II',h,12)
        assert 92<=hs<=sector
        hh=bytearray(h[:hs]);struct.pack_into('<I',hh,16,0)
        assert zlib.crc32(hh)==hc,(disk,header_lba,'header crc')
        self_lba,other_lba=struct.unpack_from('<QQ',h,24)
        assert self_lba==header_lba and other_lba==(blocks-1 if header_lba==1 else 1)
        lba,n,size,crc=struct.unpack_from('<QIII',h,72)
        assert size>=128 and size%128==0 and 0<n<=1024
        off=(lba-start)*sector;assert off>=0 and off+n*size<=len(blob)
        table=blob[off:off+n*size];assert zlib.crc32(table)==crc,(disk,header_lba,'table crc')
        parts=[]
        for i in range(n):
            p=table[i*size:(i+1)*size]
            if p[:16]==bytes(16):continue
            first,last,attrs=struct.unpack_from('<QQQ',p,32)
            name=p[56:128].decode('utf-16-le').split('\0')[0]
            parts.append(dict(index=i,name=name,first=first,last=last,attributes=f'{attrs:016x}'))
        return table,parts
    main,parts=parse(head,0,1)
    backup,otherparts=parse(tail,blocks-33,blocks-1)
    assert main==backup and parts==otherparts,(disk,'primary/backup mismatch')
    report['disks'][disk]=dict(logical_block_size=sector,total_blocks=blocks,crc_valid=True,primary_backup_equal=True,partitions=parts)
out=root/'analysis'/('gpt-'+('after' if 'after' in archive.name else 'before')+'-v135-verified.json')
out.write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
print(json.dumps(dict(boot_id=report['boot_id'],disks={d:dict(partitions=len(v['partitions']),crc_valid=True,primary_backup_equal=True) for d,v in report['disks'].items()}),indent=2))
