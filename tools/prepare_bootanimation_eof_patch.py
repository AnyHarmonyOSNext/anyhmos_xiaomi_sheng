"""Preserve checks, add the upstream zero-read break to exact donor boot player."""
from pathlib import Path
import struct,hashlib,json
r=Path(__file__).resolve().parent.parent
src=r/'work/hmos_system/system/system/bin/bootanimation'
b=src.read_bytes();sha=lambda v:hashlib.sha256(v).hexdigest()
assert sha(b)=='f019c8fbf7a263d5e4f0e6440e206bcb40b622964065b75b9da383535ba5910b'
assert b[:6]==b'\x7fELF\x02\x01'
phoff=struct.unpack_from('<Q',b,32)[0];phsize,phnum=struct.unpack_from('<HH',b,54)
loads=[]
for n in range(phnum):
 p=struct.unpack_from('<IIQQQQQQ',b,phoff+n*phsize)
 if p[0]==1:loads.append((n,p))
ex=[(n,p) for n,p in loads if p[1]&1];assert len(ex)==1
n,p=ex[0];typ,flags,off,va,pa,filesz,memsz,align=p
assert (off,va,filesz,memsz,align)==(0xd000,0xe000,0x25c30,0x25c30,0x1000)
previous=[q for _,q in loads if q[2]+q[5]<=off]
assert len(previous)==1
q=previous[0];caveoff=q[2]+q[5];assert caveoff==0xcc9c
assert not any(b[caveoff:off])
caveva=va-off+caveoff
site=0x275c8;siteoff=site-va+off
guard=bytes.fromhex('02008452621e00942009f837280340f9880900b4e902186b')
assert b[siteoff-8:siteoff+16]==guard
def ins(v):return struct.pack('<I',v)
def jump(at,to):
 delta=to-at;assert delta%4==0 and -(1<<27)<=delta<(1<<27)
 return ins(0x14000000|((delta//4)&0x3ffffff))
def cond(at,to,cc):
 delta=to-at;assert delta%4==0 and -(1<<20)<=delta<(1<<20)
 return ins(0x54000000|(((delta//4)&0x7ffff)<<5)|cc)
# n<0 still goes to the original read-error path, n==0 exits the loop,
# n>0 still executes the original null-pointer/bounds/overflow checks.
code=ins(0x7100001f)+cond(caveva+4,0x276ec,11)+cond(caveva+8,0x27604,0)+jump(caveva+12,0x275cc)
out=bytearray(b);out[caveoff:caveoff+len(code)]=code;out[siteoff:siteoff+4]=jump(site,caveva)
# Extend only the existing RX PT_LOAD backwards into a proven zero-filled gap.
# All existing section, symbol, relocation and original function VAs are unchanged.
delta=off-caveoff
newp=(typ,flags,caveoff,va-delta,pa-delta,filesz+delta,memsz+delta,align)
struct.pack_into('<IIQQQQQQ',out,phoff+n*phsize,*newp)
assert newp[2]%align==newp[3]%align
assert newp[3]+newp[6]==va+memsz
dest=r/'compat/sheng-graphics/bootanimation-eof-v1';dest.mkdir(exist_ok=True)
(dest/'bootanimation').write_bytes(out)
report=dict(input_sha256=sha(b),output_sha256=sha(out),bytes=len(out),
 input_path=str(src.relative_to(r)),patch_site_va=hex(site),patch_site_offset=siteoff,
 guard_offset=siteoff-8,guard=guard.hex(),cave_offset=caveoff,cave_va=hex(caveva),cave_bytes=code.hex(),
 old_rx=list(p),new_rx=list(newp),
 intent='ReadImageFile: break before memcpy_s when unzReadCurrentFile returns 0, preserving negative/null/bounds/overflow paths',
 source_reference='graphic_graphic_2d c19cedf62fefde6bf184aa815feeaf0346aa4d49 util.cpp lines 360-368',
 status='candidate; not device-tested')
(dest/'manifest.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
(r/'analysis/bootanimation-eof-patch.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
import base64
patches=[(phoff+n*phsize,bytes(out[phoff+n*phsize:phoff+(n+1)*phsize])),(siteoff,bytes(out[siteoff:siteoff+4])),(caveoff,code)]
spec={'name':'sheng-bootanimation-eof-v1','input_sha256':sha(b),'output_sha256':sha(out),
 'guards':[{'offset':siteoff-8,'bytes':guard.hex()},{'offset':caveoff,'bytes':bytes(len(code)).hex()}],
 'changes':[{'offset':offset,'before':b[offset:offset+len(data)].hex(),'after':data.hex()} for offset,data in patches],
 'validation':'Original native init UID1003 bootanimation read 300 PNG frames after this fix; no desktop or scanout claim.'}
(dest/'patch.json').write_text(json.dumps(spec,indent=2)+'\n',encoding='utf-8')
lines=['#!/bin/sh','set -e',"/busybox grep -q ' /hmos-root overlay ' /proc/mounts",'p=/hmos-root/system/bin/bootanimation',
 'h=$(/busybox sha256sum "$p")',f'case "$h" in {sha(b)}*) ;; *) echo INPUT_MISMATCH; exit 41;; esac',
 '/busybox cp "$p" "$p.sheng-eof-new"']
for offset,data in patches:
 lines.append(f'echo {base64.b64encode(data).decode()} | /busybox base64 -d | /busybox dd of="$p.sheng-eof-new" bs=1 seek={offset} conv=notrunc')
lines+=['h=$(/busybox sha256sum "$p.sheng-eof-new")','echo "AFTER $h"',f'case "$h" in {sha(out)}*) ;; *) echo OUTPUT_MISMATCH; exit 42;; esac',
 '/busybox chmod 755 "$p.sheng-eof-new"','/busybox mv "$p.sheng-eof-new" "$p"','echo BOOTANIMATION_EOF_INSTALLED']
(dest/'apply-ram.sh').write_bytes(('\n'.join(lines)+'\n').encode())
print(json.dumps(report,indent=2))
