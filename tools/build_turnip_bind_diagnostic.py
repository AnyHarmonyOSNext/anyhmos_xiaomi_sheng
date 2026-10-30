"""Private Mesa diagnostic build: print exact rejected OHOS bind fields."""
from pathlib import Path
import hashlib,subprocess,os,json,gzip
base=Path('/root/hmos-work/graphics-deps');r=Path('/mnt/c/SHENG_WORKSPACE')
p=base/'source/mesa3d/src/freedreno/vulkan/tu_ohos.cc';s=p.read_text()
start=s.index('VkResult tu_ohos_bind_layout(');end=s.index('VkResult tu_ohos_import_image(',start)
old=s[start:end];s=s[:start]+'''VkResult tu_ohos_bind_layout(tu_device *device,tu_image *image,const Ace5OHBufferHandle *h) {
 bool valid=tu_ohos_valid_handle(h);
 fprintf(stderr,"SHENG_BIND valid=%d vkformat=%u nativeformat=%d vkextent=%ux%u native=%dx%d stride=%d size=%d samples=%u flags=%x\\n",valid,image->vk.format,h?h->format:-1,image->vk.extent.width,image->vk.extent.height,h?h->width:-1,h?h->height:-1,h?h->stride:-1,h?h->size:-1,image->vk.samples,image->vk.create_flags);
 if(!valid || image->vk.format!=ohos_format(h->format) ||
    image->vk.extent.width!=unsigned(h->width) || image->vk.extent.height!=unsigned(h->height) ||
    image->vk.samples!=VK_SAMPLE_COUNT_1_BIT || image->vk.create_flags&VK_IMAGE_CREATE_PROTECTED_BIT)
    return VK_ERROR_INVALID_EXTERNAL_HANDLE;
 VkSubresourceLayout planes[2]={};planes[0].rowPitch=h->stride;planes[0].size=uint64_t(h->stride)*h->height;
 if(h->format==24){planes[1].offset=planes[0].size;planes[1].rowPitch=h->stride;planes[1].size=planes[0].size/2;}
 VkResult result=TU_CALLX(device,tu_image_update_layout)(device,image,DRM_FORMAT_MOD_LINEAR,planes);
 fprintf(stderr,"SHENG_BIND layout_result=%d total_size=%llu native_size=%d\\n",result,(unsigned long long)image->total_size,h->size);
 if(result!=VK_SUCCESS)return result;
 return image->total_size<=unsigned(h->size)?VK_SUCCESS:VK_ERROR_INVALID_EXTERNAL_HANDLE;
}
'''+s[end:]
if '#include <stdio.h>' not in s:s=s.replace('#include <errno.h>','#include <errno.h>\n#include <stdio.h>')
dest=r/'compat/sheng-graphics/turnip-bind-diagnostic-v1';dest.mkdir(exist_ok=True)
(dest/'tu_ohos_bind_layout.original.txt').write_text(old)
p.write_text(s);(dest/'tu_ohos.cc').write_text(s)
env=os.environ.copy();env['PATH']=str(base/'mesa-build-env/bin')+':'+env['PATH']
subprocess.run(['ninja','-C',str(base/'turnip-build'),'-j','8','src/freedreno/vulkan/libvulkan_freedreno.so'],env=env,check=True)
data=(base/'turnip-build/src/freedreno/vulkan/libvulkan_freedreno.so').read_bytes()
(dest/'libvulkan_freedreno.so').write_bytes(data)
subprocess.run(['/root/hmos-work/sdk-6.0.0.47/installed/native/llvm/bin/llvm-strip',str(dest/'libvulkan_freedreno.so')],check=True)
data=(dest/'libvulkan_freedreno.so').read_bytes()
compressed=gzip.compress(data,compresslevel=9,mtime=0)
(dest/'driver.part1').write_bytes(compressed[:900000]);(dest/'driver.part2').write_bytes(compressed[900000:])
assert len(compressed[900000:])<1048576
report={'sha256':hashlib.sha256(data).hexdigest(),'bytes':len(data),'gzip_bytes':len(compressed),'gzip_sha256':hashlib.sha256(compressed).hexdigest(),'status':'diagnostic only; same bind validation retained, added stderr fields'}
(dest/'manifest.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report))
