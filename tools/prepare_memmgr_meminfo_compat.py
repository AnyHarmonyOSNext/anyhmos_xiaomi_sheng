"""Guarded donor RAM patch: Hyperhold opt-out plus real MemAvailable in KB."""
from pathlib import Path
import hashlib
import json
import struct
import subprocess

r = Path(__file__).resolve().parent.parent
d = r / 'compat/sheng-framework/memmgr-v2'
d.mkdir(exist_ok=True)
original = (r / 'work/hmos_system/system/system/lib64/libmemmgrservice.z.so').read_bytes()
sha = lambda b: hashlib.sha256(b).hexdigest()
assert sha(original) == '8083924f66b8f3888f39b6bd400d8afbd5f21d6c02f24e553c01dcc208fc185d'
prior = json.loads((r / 'compat/sheng-framework/memmgr-v1/patch.json').read_text())
phoff = struct.unpack_from('<Q', original, 32)[0]
phsize, phnum = struct.unpack_from('<HH', original, 54)

def offset(va):
    for i in range(phnum):
        typ, flags, off, addr, _, size, _, _ = struct.unpack_from('<II6Q', original, phoff + i * phsize)
        if typ == 1 and addr <= va < addr + size:
            assert flags & 1
            return va - addr + off
    raise ValueError(hex(va))

work = r / 'work/memmgr-meminfo-v2'
work.mkdir(exist_ok=True)
linux = '/mnt/' + str(r).replace('\\', '/')[0].lower() + str(r).replace('\\', '/')[2:]
for cmd in [
    ['aarch64-linux-gnu-as', '-march=armv8.3-a', linux+'/tools/memmgr_memavailable_aarch64.S', '-o', linux+'/work/memmgr-meminfo-v2/get-current-buffer.o'],
    ['aarch64-linux-gnu-objcopy', '-O', 'binary', '--only-section=.text', linux+'/work/memmgr-meminfo-v2/get-current-buffer.o', linux+'/work/memmgr-meminfo-v2/get-current-buffer.bin'],
]:
    subprocess.run(['wsl', '-d', 'Ubuntu-22.04', '--'] + cmd, check=True)
raw = (work / 'get-current-buffer.bin').read_bytes()
start, end = 0x137444, 0x1375a0
assert len(raw) <= end - start, (len(raw), end-start)
assert len(raw) > 100
assert raw[:4] == bytes.fromhex('7f2303d5')
# There must be no unresolved external relocation in this self-contained leaf.
check = subprocess.run(['wsl', '-d', 'Ubuntu-22.04', '--', 'aarch64-linux-gnu-readelf', '-r', linux+'/work/memmgr-meminfo-v2/get-current-buffer.o'], capture_output=True, check=True, text=True)
assert 'There are no relocations' in check.stdout
changes = prior['changes'] + [dict(va=start, offset=offset(start),
    before=original[offset(start):offset(end)].hex(),
    after=(raw + bytes.fromhex('1f2003d5') * ((end-start-len(raw))//4) + bytes((end-start-len(raw))%4)).hex())]
patched = bytearray(original)
for c in changes:
    before, after = bytes.fromhex(c['before']), bytes.fromhex(c['after'])
    pos = c['offset']
    assert len(before) == len(after) and original[pos:pos+len(before)] == before
    patched[pos:pos+len(after)] = after
(d / 'libmemmgrservice.z.so').write_bytes(patched)
manifest = dict(input_sha256=sha(original), output_sha256=sha(patched), bytes=len(patched),
    changes=changes, function_bytes=len(raw), scope='Skip unsupported optional Hyperhold init; GetCurrentBuffer reads real /proc/meminfo MemAvailable in KB. Native IPC and permission checks retained; original failure sentinel retained.')
(d / 'patch.json').write_text(json.dumps(manifest, indent=2)+'\n', encoding='utf-8')
lines = ['#!/busybox sh', 'set -eu', 'B=/busybox', 'R=/hmos-root',
         'S=$R/system/lib64/libmemmgrservice.z.so', 'T=$R/compat/lib64/libmemmgrservice-meminfo-v2.z.so',
         'P=$R/compat/lib64/libmemmgrservice.z.so',
         'sum=$($B sha256sum "$S"); sum=${sum%% *}',
         f'if [ "$sum" = {sha(patched)} ]; then echo MEMMGR_MEMINFO_V2_ALREADY_STAGED=1; exit 0; fi',
         f'[ "$sum" = {sha(original)} ] || [ "$sum" = {prior["output_sha256"]} ] || exit 62',
         '$B cp "$S" "$T"']
for c in changes:
    octal = ''.join('\\%03o'%b for b in bytes.fromhex(c['after']))
    lines += [f"$B printf '{octal}' | $B dd of=\"$T\" bs=1 seek={c['offset']} conv=notrunc 2>/dev/null"]
lines += [f"echo '{sha(patched)}  '\"$T\" | $B sha256sum -c -", '$B chmod 0644 "$T"',
          '$B mount --bind "$T" "$S"', '$B touch "$P"', '$B mount --bind "$T" "$P"',
          f"echo '{sha(patched)}  '\"$S\" | $B sha256sum -c -", f"echo '{sha(patched)}  '\"$P\" | $B sha256sum -c -",
          'echo MEMMGR_REAL_MEMAVAILABLE_KB_STAGED=1']
(d / 'apply-memmgr-v2.sh').write_text('\n'.join(lines)+'\n', encoding='utf-8', newline='\n')
print(json.dumps({k: v for k, v in manifest.items() if k != 'changes'}, indent=2))
