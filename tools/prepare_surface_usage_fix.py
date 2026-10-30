"""Exact-donor candidate: native RGB imports retain color-attachment usage.

Patch the actual image creation and returned texture flags through their shared
register. Keep undefined-format/YUV imports untouched. WSL builds the fixture;
Windows runs the guarded patch generator.
"""
from pathlib import Path
import base64, hashlib, json, struct, sys, os, runpy, subprocess
r=Path(__file__).resolve().parents[1]
if '--build' in sys.argv:
    b=Path('/root/hmos-work/graphics-deps'); sdk=Path('/root/hmos-work/sdk-6.0.0.47/installed/native')
    os.environ.update(ANYHARMONYOS_OHOS_SOURCE=str(b/'source'),ANYHARMONYOS_STAGE=str(b/'stage'),ANYHARMONYOS_ROM_SYSTEM_LIBS=str(r/'work/hmos_system/system/system/lib64'),ANYHARMONYOS_SDK=str(sdk))
    cfg=runpy.run_path(str(b/'sheng-graphics-port/tools/build_adapter.py'))
    dest=r/'compat/sheng-graphics/surface-usage-v1'; dest.mkdir(exist_ok=True)
    p=dest/'native_surface_usage_probe'
    subprocess.run(cfg['COMMON']+[str(r/'tools/native_surface_usage_probe.cpp'),str(cfg['CPP']),'-o',str(p)],check=True)
    subprocess.run([str(sdk/'llvm/bin/llvm-strip'),str(p)],check=True)
    print(json.dumps(dict(bytes=p.stat().st_size,sha256=hashlib.sha256(p.read_bytes()).hexdigest())))
    sys.exit()
src=r/'compat/sheng-graphics/rosen-ohos-handle-flag-v1/librender_service_base.z.so'
data=src.read_bytes(); sha=lambda x:hashlib.sha256(x).hexdigest()
assert sha(data)=='d423413ec1fc58f40c5b04846b00530a4d82d0929eee769ede3bf5c605e5a77d'
va=0x8bdd60
phoff=struct.unpack_from('<Q',data,32)[0]; ents,num=struct.unpack_from('<HH',data,54)
segments=[struct.unpack_from('<IIQQQQQQ',data,phoff+i*ents) for i in range(num)]
matches=[s[2]+va-s[3] for s in segments if s[0]==1 and s[1]&1 and s[3]<=va<s[3]+s[5]]
assert len(matches)==1; off=matches[0]
before=struct.pack('<I',0x528000e9); after=struct.pack('<I',0x528002e9)
assert data[off:off+4]==before
guard=data[off-4:off+32]; patched=data[:off]+after+data[off+4:]
d=r/'compat/sheng-graphics/surface-usage-v1'; d.mkdir(exist_ok=True)
(d/src.name).write_bytes(patched)
report=dict(input_sha256=sha(data),output_sha256=sha(patched),va=hex(va),offset=off,before=before.hex(),after=after.hex(),guard=guard.hex(),intent='RGB external buffer import usage 0x7 -> 0x17 in both actual VkImage and original returned VKTextureInfo; YUV undefined-format path unchanged',status='candidate; independent device A/B required')
(d/'manifest.json').write_text(json.dumps(report,indent=2)+'\n')
script=['set -e','B=/busybox','R=/hmos-root','source=$R/compat/lib64/librender_service_base.z.so','p=$R/data/local/tmp/librosen-renderable.so',f'echo "{sha(data)}  $source" | $B sha256sum -c -','$B test ! -e "$p"','$B cp "$source" "$p"',f'echo {base64.b64encode(after).decode()} | $B base64 -d | $B dd of="$p" bs=1 seek={off} conv=notrunc',f'echo "{sha(patched)}  $p" | $B sha256sum -c -','$B chmod 0644 "$p"','echo SURFACE_USAGE_CANDIDATE_CREATED']
(d/'prepare-test.sh').write_text('\n'.join(script)+'\n',newline='\n')
print(json.dumps(report,indent=2))
