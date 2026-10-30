"""Add bounded native handle details to the already verified import observer."""
from pathlib import Path
import gzip, hashlib, json, os, subprocess
r=Path('/mnt/c/SHENG_WORKSPACE')
b=Path('/root/hmos-work/graphics-deps')
src=b/'source/mesa3d/src/freedreno/vulkan'
previous=r/'compat/sheng-graphics/turnip-import-diagnostic-v1'
out=r/'compat/sheng-graphics/turnip-import-diagnostic-v2'
out.mkdir(exist_ok=True)
text=(previous/'tu_device.cc').read_text()
needle='native ? (const void*)native->buffer : nullptr, h ? h->fd : -1, h ? h->size : -1);'
assert text.count(needle)==1
text=text.replace(needle,needle+'''
      if (h && result != VK_SUCCESS)
         fprintf(stderr, "SHENG_ALLOC_NATIVE n=%u valid=%d width=%d height=%d stride=%d format=%d usage=%llx reserve=%u/%u\\n",
                 n, tu_ohos_valid_handle(h), h->width, h->height, h->stride, h->format,
                 (unsigned long long)h->usage, h->reserveFds, h->reserveInts);
''')
(src/'tu_device.cc').write_text(text)
(out/'tu_device.cc').write_text(text)
env=os.environ.copy();env['PATH']=str(b/'mesa-build-env/bin')+':'+env['PATH']
subprocess.run(['ninja','-C',str(b/'turnip-build'),'-j','8','src/freedreno/vulkan/libvulkan_freedreno.so'],env=env,check=True)
p=out/'libvulkan_freedreno.so';p.write_bytes((b/'turnip-build/src/freedreno/vulkan'/p.name).read_bytes())
subprocess.run(['/root/hmos-work/sdk-6.0.0.47/installed/native/llvm/bin/llvm-strip',str(p)],check=True)
data=p.read_bytes();packed=gzip.compress(data,compresslevel=9,mtime=0)
for i,offset in enumerate(range(0,len(packed),900000),1):
    (out/f'driver.part{i}').write_bytes(packed[offset:offset+900000])
report=dict(bytes=len(data),sha256=hashlib.sha256(data).hexdigest(),gzip_bytes=len(packed),gzip_sha256=hashlib.sha256(packed).hexdigest(),changes='handle details only; original validation and results unchanged')
(out/'manifest.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report))
