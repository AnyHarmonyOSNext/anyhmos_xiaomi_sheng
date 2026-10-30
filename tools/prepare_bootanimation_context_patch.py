"""Let the donor's existing generic RenderContext setup handle Vulkan as well."""
from pathlib import Path
import struct,hashlib,json,base64
r=Path(__file__).resolve().parent.parent
src=r/'compat/sheng-graphics/bootanimation-eof-v1/bootanimation';b=src.read_bytes()
sha=lambda v:hashlib.sha256(v).hexdigest()
assert sha(b)=='1947fcb520bc5794103c2ef4777a3e0ab225640485d4d7a2c7a8934eb9f3bbd0'
site=0x170b0;siteoff=site-0x1000;caveoff=0xccac;caveva=caveoff+0x1000
assert b[siteoff-4:siteoff+12].hex()=='080140b948060034200080520f000014'
assert not any(b[caveoff:caveoff+16])
def word(v):return struct.pack('<I',v)
def jump(at,to):return word(0x14000000|(((to-at)//4)&0x3ffffff))
def cond(at,to,cc):return word(0x54000000|((((to-at)//4)&0x7ffff)<<5)|cc)
# Allow OPENGL=0 and VULKAN=1. Preserve the old return path for all other modes.
# Generic RenderContext::Create, virtual Init, SetRenderContext and every CFI/null
# check remain the original donor implementation.
code=word(0x7100051f)+cond(caveva+4,0x17178,9)+word(0x52800020)+jump(caveva+12,0x170f4)
out=bytearray(b);out[caveoff:caveoff+16]=code;out[siteoff:siteoff+4]=jump(site,caveva)
dest=r/'compat/sheng-graphics/bootanimation-context-v2';dest.mkdir(exist_ok=True)
(dest/'bootanimation').write_bytes(out)
report={'input_sha256':sha(b),'output_sha256':sha(out),'patch_site_va':hex(site),'cave_va':hex(caveva),'code':code.hex(),
 'intent':'Keep original OpenGL setup; also run the same API-selected generic RenderContext setup for Vulkan=1. No GPU-mode globals changed; null and CFI checks preserved.',
 'status':'candidate; not device-tested','depends':'bootanimation-eof-v1'}
(dest/'manifest.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
(r/'analysis/bootanimation-context-patch.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
lines=['#!/bin/sh','set -e',"/busybox grep -q ' /hmos-root overlay ' /proc/mounts",'p=/hmos-root/system/bin/bootanimation','h=$(/busybox sha256sum "$p")',f'case "$h" in {sha(b)}*) ;; *) echo INPUT_MISMATCH; exit 41;; esac','/busybox cp "$p" "$p.sheng-context-new"']
for off,data in [(siteoff,bytes(out[siteoff:siteoff+4])),(caveoff,code)]:
 lines.append(f'echo {base64.b64encode(data).decode()} | /busybox base64 -d | /busybox dd of="$p.sheng-context-new" bs=1 seek={off} conv=notrunc')
lines+=['h=$(/busybox sha256sum "$p.sheng-context-new")','echo "AFTER $h"',f'case "$h" in {sha(out)}*) ;; *) echo OUTPUT_MISMATCH; exit 42;; esac','/busybox chmod 755 "$p.sheng-context-new"','/busybox mv "$p.sheng-context-new" "$p"','echo BOOTANIMATION_CONTEXT_INSTALLED']
(dest/'apply-ram.sh').write_bytes(('\n'.join(lines)+'\n').encode())
print(json.dumps(report,indent=2))
