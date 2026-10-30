"""Observe Vulkan import results without changing validation or return values."""
from pathlib import Path
import subprocess, os, hashlib, gzip, json

r = Path('/mnt/c/SHENG_WORKSPACE')
base = Path('/root/hmos-work/graphics-deps')
src = base / 'source/mesa3d/src/freedreno/vulkan'
out = r / 'compat/sheng-graphics/turnip-import-diagnostic-v1'
out.mkdir(exist_ok=True)

wrappers = {
 'tu_image.cc': ('tu_CreateImage', r'''
VKAPI_ATTR VkResult VKAPI_CALL
tu_CreateImage(VkDevice device, const VkImageCreateInfo *info,
               const VkAllocationCallbacks *alloc, VkImage *image)
{
   VkResult result = sheng_observed_tu_CreateImage(device, info, alloc, image);
   static unsigned calls = 0, failures = 0;
   unsigned n = __atomic_add_fetch(&calls, 1, __ATOMIC_RELAXED);
   if (n <= 12 || (result != VK_SUCCESS && __atomic_add_fetch(&failures, 1, __ATOMIC_RELAXED) <= 32))
      fprintf(stderr, "SHENG_CREATE n=%u result=%d size=%ux%u format=%u usage=%x tiling=%u image=%p\n",
              n, result, info->extent.width, info->extent.height, info->format,
              info->usage, info->tiling, result == VK_SUCCESS ? (void*)*image : nullptr);
   return result;
}
'''),
 'tu_device.cc': ('tu_AllocateMemory', r'''
VKAPI_ATTR VkResult VKAPI_CALL
tu_AllocateMemory(VkDevice handle, const VkMemoryAllocateInfo *info,
                  const VkAllocationCallbacks *alloc, VkDeviceMemory *memory)
{
   VK_FROM_HANDLE(tu_device, device, handle);
   VkResult result = sheng_observed_tu_AllocateMemory(handle, info, alloc, memory);
   static unsigned calls = 0, failures = 0;
   unsigned n = __atomic_add_fetch(&calls, 1, __ATOMIC_RELAXED);
   if (n <= 12 || n % 64 == 0 || (result != VK_SUCCESS && __atomic_add_fetch(&failures, 1, __ATOMIC_RELAXED) <= 32)) {
      const auto *native = vk_find_struct_const(info->pNext, IMPORT_NATIVE_BUFFER_INFO_OHOS);
      const auto *h = native ? OH_NativeBuffer_GetBufferHandle(native->buffer) : nullptr;
      fprintf(stderr, "SHENG_ALLOC n=%u result=%d requested=%llu type=%u heap_used=%llu heap_size=%llu native=%p fd=%d native_size=%d\n",
              n, result, (unsigned long long)info->allocationSize, info->memoryTypeIndex,
              (unsigned long long)p_atomic_read(&device->physical_device->heap.used),
              (unsigned long long)device->physical_device->heap.size,
              native ? (const void*)native->buffer : nullptr, h ? h->fd : -1, h ? h->size : -1);
   }
   return result;
}
'''),
 'tu_ohos.cc': ('tu_GetNativeBufferPropertiesOHOS', r'''
VKAPI_ATTR VkResult VKAPI_CALL
tu_GetNativeBufferPropertiesOHOS(VkDevice device, const OH_NativeBuffer *buffer,
                                 VkNativeBufferPropertiesOHOS *out)
{
   VkResult result = sheng_observed_tu_GetNativeBufferPropertiesOHOS(device, buffer, out);
   static unsigned calls = 0, failures = 0;
   unsigned n = __atomic_add_fetch(&calls, 1, __ATOMIC_RELAXED);
   if (n <= 12 || (result != VK_SUCCESS && __atomic_add_fetch(&failures, 1, __ATOMIC_RELAXED) <= 32))
      fprintf(stderr, "SHENG_PROPERTIES n=%u result=%d native=%p size=%llu types=%x\n",
              n, result, (const void*)buffer, out ? (unsigned long long)out->allocationSize : 0,
              out ? out->memoryTypeBits : 0);
   return result;
}
''')}

for filename, (name, wrapper) in wrappers.items():
    p = src / filename
    text = p.read_text()
    backup = out / (filename + '.original')
    if not backup.exists():
        assert 'sheng_observed_' not in text
        backup.write_text(text)
    else:
        text = backup.read_text()
    needle = name + '('
    assert text.count(needle) >= 1
    # First occurrence in these pinned files is the function definition.
    pos = text.index(needle)
    assert 'VKAPI_ATTR' in text[max(0, pos-80):pos]
    text = text[:pos] + 'sheng_observed_' + text[pos:]
    text = '#include <stdio.h>\n' + text + '\n' + wrapper
    p.write_text(text)
    (out / filename).write_text(text)

env = os.environ.copy()
env['PATH'] = str(base / 'mesa-build-env/bin') + ':' + env['PATH']
subprocess.run(['ninja', '-C', str(base / 'turnip-build'), '-j', '8',
                'src/freedreno/vulkan/libvulkan_freedreno.so'], env=env, check=True)
lib = out / 'libvulkan_freedreno.so'
lib.write_bytes((base / 'turnip-build/src/freedreno/vulkan/libvulkan_freedreno.so').read_bytes())
subprocess.run(['/root/hmos-work/sdk-6.0.0.47/installed/native/llvm/bin/llvm-strip', str(lib)], check=True)
data = lib.read_bytes()
packed = gzip.compress(data, compresslevel=9, mtime=0)
for i, offset in enumerate(range(0, len(packed), 900000), 1):
    (out / f'driver.part{i}').write_bytes(packed[offset:offset+900000])
report = dict(bytes=len(data), sha256=hashlib.sha256(data).hexdigest(),
              gzip_bytes=len(packed), gzip_sha256=hashlib.sha256(packed).hexdigest(),
              changes='read-only result and heap accounting logs; original import validation retained')
(out / 'manifest.json').write_text(json.dumps(report, indent=2)+'\n')
print(json.dumps(report))
