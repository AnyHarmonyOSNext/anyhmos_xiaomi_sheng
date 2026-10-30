"""Exact donor's private OHOS handle flag -> deployed port header flag."""
from pathlib import Path
import struct,json,hashlib,base64
r=Path(__file__).resolve().parent.parent
src=r/'work/donor-hdi-link/librender_service_base.z.so';b=src.read_bytes();sha=lambda x:hashlib.sha256(x).hexdigest()
assert sha(b)=='0a699e2317dab4699117a90e7e21d5727bd823e3474a70ebaed4d32667e519ff'
va=0x8bcaf4;off=va-0x1000
guard=b[off-8:off+12];assert guard.hex()=='aac300d1a9031db8090090520b008152670040b9'
before=b[off:off+4];after=struct.pack('<I',0x52840009)
assert before.hex()=='09009052'
out=b[:off]+after+b[off+4:]
dest=r/'compat/sheng-graphics/rosen-ohos-handle-flag-v1';dest.mkdir(exist_ok=True)
(dest/'librender_service_base.z.so').write_bytes(out)
spec={'name':'sheng-rosen-ohos-handle-flag-v1','input_sha256':sha(b),'output_sha256':sha(out),
 'guards':[{'offset':off-8,'bytes':guard.hex()}],'changes':[{'offset':off,'before':before.hex(),'after':after.hex()}],
 'validation':'candidate, not yet device-tested','intent':'Only NativeBufferUtils::CreateVkImage OHOS external memory flag 0x8000 -> deployed Mesa OHOS flag 0x2000; token, caller, permissions and CFI unchanged'}
(dest/'patch.json').write_text(json.dumps(spec,indent=2)+'\n',encoding='utf-8')
(r/'analysis/rosen-ohos-handle-flag-patch.json').write_text(json.dumps(spec,indent=2)+'\n',encoding='utf-8')
lines=['#!/bin/sh','set -e',"/busybox grep -q ' /hmos-root overlay ' /proc/mounts",'p=/hmos-root/system/lib64/librender_service_base.z.so','h=$(/busybox sha256sum "$p")',f'case "$h" in {sha(b)}*) ;; *) echo INPUT_MISMATCH; exit 41;; esac',
 '/busybox cp "$p" "$p.sheng-flag-new"',f'echo {base64.b64encode(after).decode()} | /busybox base64 -d | /busybox dd of="$p.sheng-flag-new" bs=1 seek={off} conv=notrunc',
 'h=$(/busybox sha256sum "$p.sheng-flag-new")','echo "AFTER $h"',f'case "$h" in {sha(out)}*) ;; *) echo OUTPUT_MISMATCH; exit 42;; esac',
 '/busybox chmod 644 "$p.sheng-flag-new"','/busybox mv "$p.sheng-flag-new" "$p"','echo ROSEN_OHOS_HANDLE_FLAG_INSTALLED']
(dest/'apply-ram.sh').write_bytes(('\n'.join(lines)+'\n').encode())
print(json.dumps(spec,indent=2))
