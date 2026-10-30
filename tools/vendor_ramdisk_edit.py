"""Checked vendor_boot v4 edits retaining every unrelated cpio/container byte."""
import hashlib
import struct
import subprocess

sha = lambda b: hashlib.sha256(b).hexdigest()
MAGISKBOOT = 'C:/MIO-KITCHEN-PYSIDE6-5.0.0-PREVIEW/bin/Windows/AMD64/magiskboot.exe'

def parse(b):
    pos, result = 0, {}
    while b[pos:pos+6] == b'070701':
        f = [int(b[pos+6+i*8:pos+14+i*8],16) for i in range(13)]
        n = b[pos+110:pos+109+f[11]].decode()
        start = (pos+110+f[11]+3)&~3
        if n == 'TRAILER!!!': return result
        assert n not in result
        result[n] = (f,b[start:start+f[6]])
        pos = (start+f[6]+3)&~3
    raise ValueError('Invalid cpio')

def pack(entries):
    out = bytearray()
    for name,(fields,blob) in list(entries.items())+[('TRAILER!!!',([0]*13,b''))]:
        f=fields.copy();nb=name.encode()+b'\0';f[6],f[11],f[12]=len(blob),len(nb),0
        out.extend(b'070701'+''.join(f'{v:08x}' for v in f).encode()+nb)
        out.extend(bytes((-len(out))%4));out.extend(blob);out.extend(bytes((-len(out))%4))
    out.extend(bytes((-len(out))%512));return out

def edit(base_path, expected_sha, work, mutate, allowed, added=()):
    work.mkdir(exist_ok=True)
    base=base_path.read_bytes();assert sha(base)==expected_sha
    version,page=struct.unpack_from('<II',base,8);hs,ds=struct.unpack_from('<II',base,2096)
    ts,ne,es,bs=struct.unpack_from('<IIII',base,2112)
    assert base[:8]==b'VNDRBOOT' and (version,hs,ne)==(4,2128,1)
    align=lambda x:(x+page-1)//page*page
    rs=align(hs);size=struct.unpack_from('<I',base,24)[0]
    dt=rs+align(size);tt=dt+align(ds);bc=tt+align(ts)
    (work/'base.lz4').write_bytes(base[rs:rs+size])
    subprocess.run([MAGISKBOOT,'decompress',str(work/'base.lz4'),str(work/'base.cpio')],check=True,capture_output=True)
    old=parse((work/'base.cpio').read_bytes());new=dict(old)
    added=set(added)
    assert not added.intersection(old) and added.issubset(allowed)
    mutate(new)
    assert set(new)==set(old).union(added)
    assert all(new[n]==v for n,v in old.items() if n not in allowed)
    raw=pack(new);new=parse(raw);(work/'ramdisk.cpio').write_bytes(raw)
    subprocess.run([MAGISKBOOT,'compress=lz4_legacy',str(work/'ramdisk.cpio'),str(work/'ramdisk.lz4')],check=True,capture_output=True)
    compressed=(work/'ramdisk.lz4').read_bytes()
    table=bytearray(base[tt:tt+ts]);assert struct.unpack_from('<II',table)==(size,0)
    struct.pack_into('<I',table,0,len(compressed))
    image=bytearray(base[:rs]);struct.pack_into('<I',image,24,len(compressed))
    for blob in [compressed,base[dt:dt+ds],table,base[bc:bc+bs]]:
        image.extend(blob);image.extend(bytes((-len(image))%page))
    assert len(image)<len(base)-4096
    image.extend(bytes(len(base)-len(image)))
    (work/'roundtrip.lz4').write_bytes(image[rs:rs+len(compressed)])
    subprocess.run([MAGISKBOOT,'decompress',str(work/'roundtrip.lz4'),str(work/'roundtrip.cpio')],check=True,capture_output=True)
    assert parse((work/'roundtrip.cpio').read_bytes())==new
    ndt=rs+align(len(compressed));ntt=ndt+align(ds);nbc=ntt+align(ts)
    assert image[ndt:ndt+ds]==base[dt:dt+ds] and image[nbc:nbc+bs]==base[bc:bc+bs]
    hdr=bytearray(image[:rs]);struct.pack_into('<I',hdr,24,size);assert hdr==base[:rs]
    tab=bytearray(image[ntt:ntt+ts]);struct.pack_into('<I',tab,0,size);assert tab==base[tt:tt+ts]
    return image
