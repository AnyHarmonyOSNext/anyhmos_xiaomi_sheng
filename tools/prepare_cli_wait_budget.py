"""Keep the original optional CLI provider/IPC; bound only its synchronous wait."""
from pathlib import Path
import hashlib
import json
import struct

r = Path(__file__).resolve().parent.parent
p = r/'work/hmos_system/system/system/lib64/platformsdk/libcli_tool_client.z.so'
b = p.read_bytes()
sha = lambda x: hashlib.sha256(x).hexdigest()
assert sha(b) == '729f4999e99d6dc9eb83eceda08dc9e68a4369ab8e057d450c8d5f7448b64910'
phoff = struct.unpack_from('<Q', b, 32)[0]
phsize, phnum = struct.unpack_from('<HH', b, 54)
def offset(va):
    for i in range(phnum):
        typ, flags, off, addr, _, size, _, _ = struct.unpack_from('<II6Q', b, phoff+i*phsize)
        if typ == 1 and addr <= va < addr+size:
            assert flags & 1
            return off+va-addr
    raise ValueError(hex(va))
changes=[]
for va, before, after in [(0x23e20, '08008552', '08209c52'),
                          (0x23e2c, '68cdbd72', 'a8bea072')]:
    pos=offset(va)
    assert b[pos:pos+4].hex()==before, (hex(va), b[pos:pos+4].hex())
    changes.append(dict(va=va, offset=pos, before=before, after=after))
# MOVZ/MOVK form exactly 100,000,000 nanoseconds instead of 4,000,000,000.
def imm(word): return (word>>5)&0xffff
assert imm(int.from_bytes(bytes.fromhex(changes[0]['after']),'little'))==0xe100
assert imm(int.from_bytes(bytes.fromhex(changes[1]['after']),'little'))==0x5f5
patched=bytearray(b)
for c in changes: patched[c['offset']:c['offset']+4]=bytes.fromhex(c['after'])
d=r/'compat/sheng-framework/cli-wait-v1';d.mkdir(exist_ok=True)
(d/p.name).write_bytes(patched)
(d/'patch.json').write_text(json.dumps(dict(input_sha256=sha(b),output_sha256=sha(patched),
    changes=changes,old_ns=4000000000,new_ns=100000000,
    scope='Original async LoadSystemAbility, callback, permission/CFI checks, cached proxy, failure result and cleanup retained. Bound only the client wait for optional missing SA186.'),indent=2)+'\n',encoding='utf-8')
lines=['#!/busybox sh','set -eu','B=/busybox','R=/hmos-root',
       'S=$R/system/lib64/platformsdk/libcli_tool_client.z.so',
       'T=$R/compat/lib64/libcli_tool_client.z.so',
       'sum=$($B sha256sum "$S"); sum=${sum%% *}',
       f'if [ "$sum" = {sha(patched)} ]; then echo CLI_WAIT_ALREADY_STAGED=1; exit 0; fi',
       f'[ "$sum" = {sha(b)} ] || exit 62','$B cp "$S" "$T"']
for c in changes:
    octal=''.join('\\%03o'%x for x in bytes.fromhex(c['after']))
    lines += [f"$B printf '{octal}' | $B dd of=\"$T\" bs=1 seek={c['offset']} conv=notrunc 2>/dev/null"]
lines += [f"echo '{sha(patched)}  '\"$T\" | $B sha256sum -c -",'$B chmod 0644 "$T"',
          '$B mount --bind "$T" "$S"','echo OPTIONAL_CLI_WAIT_BUDGET_100MS_STAGED=1']
(d/'apply-cli-wait-v1.sh').write_text('\n'.join(lines)+'\n',encoding='utf-8',newline='\n')
print(json.dumps({'input':sha(b),'output':sha(patched),'changes':changes},indent=2))
