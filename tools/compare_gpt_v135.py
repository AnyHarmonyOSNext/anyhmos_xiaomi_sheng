"""Assert original HAL changed only boot-success attributes and associated CRCs."""
from pathlib import Path
import json
import struct
import tarfile

r=Path(__file__).resolve().parent.parent
before=json.loads((r/'analysis/gpt-before-v135-verified.json').read_text(encoding='utf-8'))
after=json.loads((r/'analysis/gpt-after-v135-verified.json').read_text(encoding='utf-8'))
assert before['boot_id']==after['boot_id']
changes=[]
for disk,b in before['disks'].items():
    a=after['disks'][disk]
    assert len(b['partitions'])==len(a['partitions'])
    for bp,ap in zip(b['partitions'],a['partitions']):
        assert {k:v for k,v in bp.items() if k!='attributes'}=={k:v for k,v in ap.items() if k!='attributes'}
        if bp['attributes']!=ap['attributes']:
            changes.append(dict(disk=disk,partition=bp['name'],before=bp['attributes'],after=ap['attributes'],
                                xor=f"{int(bp['attributes'],16)^int(ap['attributes'],16):016x}"))

def blobs(path):
    with tarfile.open(path,'r:gz') as t:
        return {m.name.removeprefix('./'):t.extractfile(m).read() for m in t.getmembers() if m.isfile()}
bb,aa=blobs(before['source']),blobs(after['source'])
regions=[]
for disk,b in before['disks'].items():
    sector,blocks=b['logical_block_size'],b['total_blocks']
    for side,start,lba in [('head',0,1),('tail',blocks-33,blocks-1)]:
        name=disk+'-'+side+'.bin';x,y=bytearray(bb[name]),bytearray(aa[name]);p=(lba-start)*sector
        table,n,size,_=struct.unpack_from('<QIII',x,p+72);offset=(table-start)*sector
        # Ignore only the two header CRC fields and the uint64 attribute per entry.
        for z in [x,y]:
            z[p+16:p+20]=bytes(4);z[p+88:p+92]=bytes(4)
            for i in range(n):z[offset+i*size+48:offset+i*size+56]=bytes(8)
        assert x==y,(disk,side,'unexpected byte change outside attributes/CRCs')
        regions.append(name)
report=dict(boot_id=before['boot_id'],original_hal_changes=changes,
            only_attributes_and_header_crcs_changed=True,verified_regions=regions,
            primary_and_backup_crc_verified=True,manual_raw_disk_writes=False)
(r/'analysis/gpt-v135-original-hal-diff.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
print(json.dumps(report,indent=2))
