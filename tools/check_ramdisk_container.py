"""Preflight real vendor+generic ramdisk compression boundary (read-only).

The exact kernel unlz4() loops over legacy LZ4 blocks, accepting another LZ4
magic, not a gzip stream. Kernel gzip support alone is insufficient here.
This is an offline format check, not a substitute for device boot logs.
"""
from pathlib import Path
import struct,json,sys
r=Path(__file__).resolve().parent.parent
vendor=(r/'output/vendor_boot_stock_303.img').read_bytes()
assert vendor[:8]==b'VNDRBOOT'
page=struct.unpack_from('<I',vendor,12)[0]
size=struct.unpack_from('<I',vendor,24)[0]
header=struct.unpack_from('<I',vendor,2096)[0]
start=(header+page-1)//page*page
raw=vendor[start:start+size]
MAGIC=0x184c2102;assert struct.unpack_from('<I',raw)[0]==MAGIC
offset=4;blocks=0;archives=1
while offset+4<=len(raw):
    n=struct.unpack_from('<I',raw,offset)[0]
    if n==MAGIC:offset+=4;archives+=1;continue
    if n==0:break
    assert n<=8*1024*1024+65536 and offset+4+n<=len(raw),(offset,n,len(raw))
    offset+=4+n;blocks+=1
report={'vendor_ramdisk_bytes':size,'vendor_legacy_lz4_archives':archives,'vendor_blocks':blocks,'vendor_parsed_bytes':offset,'vendor_tail_hex':raw[offset:offset+16].hex(),'versions':{}}
for label in ['v37','v38','v39']:
    image=(r/f'output/init_boot_hmos_probe_{label}.img').read_bytes()
    length=struct.unpack_from('<I',image,12)[0];payload=image[4096:4096+length]
    matched=payload[:4]==struct.pack('<I',MAGIC)
    report['versions'][label]={'compression_magic':payload[:8].hex(),'bytes':length,'matches_vendor_legacy_lz4':matched,'cold_boot_verified':label=='v37'}
assert offset==len(raw),'Vendor has a terminator/padding; inspect exact concatenation before inference'
report['finding']='Vendor legacy-LZ4 ends at a block boundary without a zero terminator; if bootloader concatenates generic ramdisk directly, v38 gzip bytes are misread as an LZ4 block. v39 retains matching legacy-LZ4 framing. Device failure cause remains pending Recovery logs.'
(r/'analysis/ramdisk-container-preflight.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps(report,indent=2))
if len(sys.argv)>1:assert report['versions'][sys.argv[1]]['matches_vendor_legacy_lz4'],'Rejected mixed compression at vendor ramdisk boundary'
