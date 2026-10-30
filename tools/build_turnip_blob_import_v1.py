"""Support real one-dimensional OHOS BLOB memory without making it an image.

The current allocator already emits page-backed BLOBs for compressed ASTC data.
Keep all existing RGB/YUV image validation, and validate BLOB imports separately.
"""
from pathlib import Path
import gzip, hashlib, json, os, subprocess
r = Path('/mnt/c/SHENG_WORKSPACE')
b = Path('/root/hmos-work/graphics-deps')
src = b/'source/mesa3d/src/freedreno/vulkan'
out = r/'compat/sheng-graphics/blob-import-v1'
out.mkdir(exist_ok=True)
for name in ['tu_ohos.h', 'tu_ohos.cc', 'tu_device.cc']:
    before = out/(name+'.before')
    if not before.exists(): before.write_bytes((src/name).read_bytes())
h = (out/'tu_ohos.h.before').read_text()
h = h.replace('bool tu_ohos_valid_handle(const Ace5OHBufferHandle *);',
              'bool tu_ohos_valid_handle(const Ace5OHBufferHandle *);\nbool tu_ohos_valid_blob_handle(const Ace5OHBufferHandle *);')
text = (out/'tu_ohos.cc.before').read_text()
marker = 'bool tu_ohos_valid_handle(const Ace5OHBufferHandle *h) {'
assert text.count(marker) == 1
text = text.replace(marker, '''// BLOB width/stride are byte counts, not image dimensions. Never admit this
// format through image validation or advertise image sampling/render features.
bool tu_ohos_valid_blob_handle(const Ace5OHBufferHandle *h) {
 if(!h || h->fd<0 || h->format!=38 || h->width<=0 || h->width>256*1024*1024 ||
    h->height!=1 || h->stride!=h->width || h->size<=0 || h->reserveFds || h->reserveInts ||
    (h->usage & ((1ULL<<11)|(7ULL<<8)))) return false;
 uint64_t page_size=(uint64_t(h->width)+4095)&~uint64_t(4095);
 return uint64_t(h->size)==page_size;
}
''' + marker)
text = text.replace('if(!out || !tu_ohos_valid_handle(h)) {',
                    'if(!out || (!tu_ohos_valid_handle(h) && !tu_ohos_valid_blob_handle(h))) {')
marker = '  // Rosen/Skia imports NV12 through its external YCbCr texture path.'
assert text.count(marker) == 1
text = text.replace(marker, '''  if(h->format==38) {
   f->format=VK_FORMAT_UNDEFINED;f->externalFormat=0;f->formatFeatures=0;
   f->samplerYcbcrConversionComponents={VK_COMPONENT_SWIZZLE_IDENTITY,VK_COMPONENT_SWIZZLE_IDENTITY,VK_COMPONENT_SWIZZLE_IDENTITY,VK_COMPONENT_SWIZZLE_IDENTITY};
   f->suggestedYcbcrModel=VK_SAMPLER_YCBCR_MODEL_CONVERSION_RGB_IDENTITY;
   f->suggestedYcbcrRange=VK_SAMPLER_YCBCR_RANGE_ITU_FULL;
   f->suggestedXChromaOffset=f->suggestedYChromaOffset=VK_CHROMA_LOCATION_COSITED_EVEN;
   return VK_SUCCESS;
  }
''' + marker)
device = (out/'tu_device.cc.before').read_text()
old = '      if (!tu_ohos_valid_handle(h) || pAllocateInfo->allocationSize < (uint64_t)h->size) {'
assert device.count(old) == 1
device = device.replace(old, '''      const bool blob = tu_ohos_valid_blob_handle(h);
      const auto *dedicated = vk_find_struct_const(pAllocateInfo->pNext, MEMORY_DEDICATED_ALLOCATE_INFO);
      const uint64_t blob_min = blob ? (uint64_t(h->width)+63)&~uint64_t(63) : 0;
      const bool valid_size = blob ?
         (pAllocateInfo->allocationSize >= blob_min && pAllocateInfo->allocationSize <= uint64_t(h->size) &&
          (!dedicated || dedicated->image == VK_NULL_HANDLE)) :
         (tu_ohos_valid_handle(h) && pAllocateInfo->allocationSize >= uint64_t(h->size));
      if (!valid_size) {''')
old = '      if (result == VK_SUCCESS) {\n         mem->ohos_handle = *h;'
assert device.count(old) == 1
device = device.replace(old, '''      if (result == VK_SUCCESS && blob && mem->bo->size < uint64_t(h->size)) {
         tu_bo_finish(device, mem->bo);
         result = VK_ERROR_INVALID_EXTERNAL_HANDLE;
      }
      if (result == VK_SUCCESS) {
         if (blob) {
            static unsigned blobs = 0;
            unsigned n = __atomic_add_fetch(&blobs, 1, __ATOMIC_RELAXED);
            if(n<=12 || n%256==0)fprintf(stderr,"SHENG_BLOB_IMPORT n=%u bytes=%d requested=%llu backing=%llu\\n",n,h->width,(unsigned long long)pAllocateInfo->allocationSize,(unsigned long long)mem->bo->size);
         }
         mem->ohos_handle = *h;''')
for name, content in [('tu_ohos.h',h),('tu_ohos.cc',text),('tu_device.cc',device)]:
    (src/name).write_text(content)
    (out/name).write_text(content)
env = os.environ.copy();env['PATH'] = str(b/'mesa-build-env/bin')+':'+env['PATH']
subprocess.run(['ninja','-C',str(b/'turnip-build'),'-j','8','src/freedreno/vulkan/libvulkan_freedreno.so'],env=env,check=True)
p=out/'libvulkan_freedreno.so'
p.write_bytes((b/'turnip-build/src/freedreno/vulkan'/p.name).read_bytes())
subprocess.run(['/root/hmos-work/sdk-6.0.0.47/installed/native/llvm/bin/llvm-strip',str(p)],check=True)
data=p.read_bytes();packed=gzip.compress(data,compresslevel=9,mtime=0)
for i,offset in enumerate(range(0,len(packed),900000),1):
    (out/f'driver.part{i}').write_bytes(packed[offset:offset+900000])
report=dict(bytes=len(data),sha256=hashlib.sha256(data).hexdigest(),gzip_bytes=len(packed),gzip_sha256=hashlib.sha256(packed).hexdigest(),
            changes='Separate bounded 1D BLOB memory import; RGB/YUV image validation preserved; BLOB image usage and dedicated images rejected; page backing verified')
(out/'manifest.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps(report))
