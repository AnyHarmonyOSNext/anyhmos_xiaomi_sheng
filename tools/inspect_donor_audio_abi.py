"""Save focused donor disassembly and compressed debug symbols (run in WSL)."""
from pathlib import Path
import lzma
import re
import struct
import subprocess

r = Path(__file__).resolve().parent.parent
base = r/'work/donor-audio-hdi'
report = []
for p in sorted(base.rglob('*.so')):
    b = p.read_bytes()
    off = struct.unpack_from('<Q', b, 40)[0]
    size, count, names_index = struct.unpack_from('<HHH', b, 58)
    sec = [struct.unpack_from('<IIQQQQIIQQ', b, off+i*size) for i in range(count)]
    ns = sec[names_index]
    names = b[ns[4]:ns[4]+ns[5]]
    for s in sec:
        name = names[s[0]:].split(b'\0', 1)[0]
        if name == b'.gnu_debugdata':
            debug = p.with_suffix('.debug.elf')
            debug.write_bytes(lzma.decompress(b[s[4]:s[4]+s[5]]))
    d = subprocess.check_output(['aarch64-linux-gnu-objdump', '-d', str(p)], text=True)
    (r/'analysis'/(p.name+'.disasm.txt')).write_text(d)
    report.append('\nFILE '+p.name)
    funcs = re.split(r'\n(?=[0-9a-f]+ <)', d)
    for f in funcs:
        first = f.splitlines()[0] if f else ''
        if any(x in first for x in ['GetAllAdapters', 'LoadAdapter', 'GetPortCapability',
                                    'AttrsToVdiAttrs', 'CreateRenderById', 'RenderFrameVdi',
                                    'AudioRenderStartVdi', 'AudioManagerCreateIfInstance']):
            report.append(first)
            lines = f.splitlines()
            for i, line in enumerate(lines):
                if '\tblr\t' in line:
                    report.extend(lines[max(1, i-8):i+2])
    if 'primary_impl_vendor' in p.name:
        symbols = subprocess.check_output(['aarch64-linux-gnu-nm', '-C', str(p.with_suffix('.debug.elf'))], text=True)
        (r/'analysis/donor-audio-vdi-debug-symbols.txt').write_text(symbols)
(r/'analysis/donor-audio-abi-calls.txt').write_text('\n'.join(report)+'\n')
print('\n'.join(report))

p=base/'vendor/lib64/libaudio_primary_impl_vendor.z.so'
symbols={}
for path, flags in [(p,['-D']),(p.with_suffix('.debug.elf'),[])]:
    text=subprocess.check_output(['aarch64-linux-gnu-nm',*flags,'-S','--defined-only',str(path)],text=True)
    for line in text.splitlines():
        m=re.match(r'([0-9a-f]+) ([0-9a-f]+) [Tt] (\w+)$',line)
        if m: symbols[m[3]]=(int(m[1],16),int(m[2],16))
text=(r/'analysis'/(p.name+'.disasm.txt')).read_text()
instructions=[]
for line in text.splitlines():
    m=re.match(r'\s*([0-9a-f]+):\s+\w+\s+(.*)',line)
    if m: instructions.append((int(m[1],16),m[2]))
out=[]
for name,(addr,size) in sorted(symbols.items(),key=lambda kv:kv[1]):
    if not name.endswith('Vdi'): continue
    lines=[(a,t) for a,t in instructions if addr<=a<addr+size]
    for i,(a,t) in enumerate(lines):
        if t.startswith('blr'):
            # Preserve preceding instructions as evidence, not a guessed ABI.
            out.append(name+'\n'+'\n'.join(f'{a:x}: {t}' for a,t in lines[max(0,i-10):i+1]))
(r/'analysis/donor-audio-vdi-indirect-calls.txt').write_text('\n\n'.join(out)+'\n')
print('Saved all VDI indirect-call evidence')
