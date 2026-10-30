// Real VDI DMA-BUF -> VkBuffer import -> GPU copy -> CPU byte verification.
// The original SurfaceBuffer owns a genuine allocator handle (pinned donor ABI).
#define VK_USE_PLATFORM_OHOS
#include <vulkan/vulkan.h>
#include "idisplay_buffer_vdi.h"
#include <cstdio>
#include <cstdint>
#include <cstdlib>
#include <cstring>
#include <dlfcn.h>
#include <unistd.h>
using namespace OHOS::HDI::Display::Buffer::V1_0;
struct NativeRef { void *p; ~NativeRef() {} };
#define CHECK(x) do { if (!(x)) { printf("FAIL line=%d %s\n",__LINE__,#x); _exit(1); } } while(0)
#define VKCHECK(x) do { VkResult result=(x); if(result!=VK_SUCCESS) { printf("FAIL line=%d result=%d %s\n",__LINE__,result,#x); _exit(2); } } while(0)
#define INST(n) auto n=reinterpret_cast<PFN_##n>(gipa(instance,#n));CHECK(n)
#define DEV(n) auto n=reinterpret_cast<PFN_##n>(vkGetDeviceProcAddr(device,#n));CHECK(n)
int main(int argc,char **argv)
{
 setbuf(stdout,nullptr);alarm(25);CHECK(argc==2);
 auto native=dlopen("libnative_buffer.so",RTLD_NOW|RTLD_GLOBAL);CHECK(native);
 auto create=reinterpret_cast<NativeRef(*)()>(dlsym(native,"_ZN4OHOS13SurfaceBuffer6CreateEv"));CHECK(create);
 auto vlib=dlopen("/compat/lib64/libdisplay_buffer_vdi_impl.z.so",RTLD_NOW|RTLD_LOCAL);CHECK(vlib);
 auto factory=reinterpret_cast<CreateDisplayBufferVdiFunc>(dlsym(vlib,"CreateDisplayBufferVdi"));CHECK(factory);
 auto vdi=factory();CHECK(vdi);
 constexpr unsigned logical=18512, guards=128;
 BufferHandle *h=nullptr;CHECK(vdi->AllocMem({logical,1,0x2b,38,0},h)==0&&h);
 CHECK(h->height==1&&h->width==logical&&h->stride==logical&&h->size==20480);
 CHECK(vdi->Mmap(*h)!=nullptr);CHECK(h->virAddr);
 auto bytes=static_cast<unsigned char*>(h->virAddr);
 for(unsigned i=0;i<logical;i++)bytes[i]=(i*37+19)&255;
 std::memset(bytes+logical,0xe7,h->size-logical);
 CHECK(vdi->FlushCache(*h)==0);
 auto owner=create();CHECK(owner.p);
 auto field=reinterpret_cast<BufferHandle**>(static_cast<char*>(owner.p)+16);CHECK(!*field);*field=h;
 auto buffer=reinterpret_cast<OH_NativeBuffer*>(owner.p);
 auto driver=dlopen(argv[1],RTLD_NOW|RTLD_LOCAL);if(!driver)puts(dlerror());CHECK(driver);
 auto gipa=reinterpret_cast<PFN_vkGetInstanceProcAddr>(dlsym(driver,"vk_icdGetInstanceProcAddr"));CHECK(gipa);
 VkInstance instance=VK_NULL_HANDLE;INST(vkCreateInstance);
 VkApplicationInfo app{VK_STRUCTURE_TYPE_APPLICATION_INFO};app.apiVersion=VK_API_VERSION_1_1;
 VkInstanceCreateInfo ici{VK_STRUCTURE_TYPE_INSTANCE_CREATE_INFO};ici.pApplicationInfo=&app;
 VKCHECK(vkCreateInstance(&ici,nullptr,&instance));
 INST(vkEnumeratePhysicalDevices);INST(vkCreateDevice);INST(vkGetDeviceProcAddr);INST(vkGetPhysicalDeviceMemoryProperties);INST(vkDestroyInstance);
 uint32_t count=1;VkPhysicalDevice physical;VKCHECK(vkEnumeratePhysicalDevices(instance,&count,&physical));CHECK(count);
 float priority=1;VkDeviceQueueCreateInfo q{VK_STRUCTURE_TYPE_DEVICE_QUEUE_CREATE_INFO};q.queueCount=1;q.pQueuePriorities=&priority;
 const char *exts[]={"VK_OHOS_external_memory","VK_OHOS_native_buffer"};
 VkDeviceCreateInfo d{VK_STRUCTURE_TYPE_DEVICE_CREATE_INFO};d.queueCreateInfoCount=1;d.pQueueCreateInfos=&q;d.enabledExtensionCount=2;d.ppEnabledExtensionNames=exts;
 VkDevice device;VKCHECK(vkCreateDevice(physical,&d,nullptr,&device));
 DEV(vkCreateBuffer);DEV(vkGetBufferMemoryRequirements);DEV(vkAllocateMemory);DEV(vkBindBufferMemory);DEV(vkGetNativeBufferPropertiesOHOS);
 DEV(vkMapMemory);DEV(vkUnmapMemory);DEV(vkGetDeviceQueue);DEV(vkCreateCommandPool);DEV(vkAllocateCommandBuffers);
 DEV(vkBeginCommandBuffer);DEV(vkCmdCopyBuffer);DEV(vkCmdPipelineBarrier);DEV(vkEndCommandBuffer);DEV(vkQueueSubmit);DEV(vkQueueWaitIdle);
 DEV(vkDestroyCommandPool);DEV(vkDestroyBuffer);DEV(vkFreeMemory);DEV(vkDestroyDevice);
 VkExternalMemoryBufferCreateInfo ext{VK_STRUCTURE_TYPE_EXTERNAL_MEMORY_BUFFER_CREATE_INFO};ext.handleTypes=VK_EXTERNAL_MEMORY_HANDLE_TYPE_OHOS_NATIVE_BUFFER_BIT_OHOS;
 VkBufferCreateInfo bi{VK_STRUCTURE_TYPE_BUFFER_CREATE_INFO};bi.pNext=&ext;bi.size=logical;bi.usage=VK_BUFFER_USAGE_TRANSFER_SRC_BIT;
 VkBuffer source;VKCHECK(vkCreateBuffer(device,&bi,nullptr,&source));
 VkMemoryRequirements req;vkGetBufferMemoryRequirements(device,source,&req);
 printf("BLOB_LAYOUT logical=%u requirement=%llu backing=%d\n",logical,(unsigned long long)req.size,h->size);
 VkNativeBufferFormatPropertiesOHOS fmt{VK_STRUCTURE_TYPE_NATIVE_BUFFER_FORMAT_PROPERTIES_OHOS};
 VkNativeBufferPropertiesOHOS props{VK_STRUCTURE_TYPE_NATIVE_BUFFER_PROPERTIES_OHOS};props.pNext=&fmt;
 VkResult query=vkGetNativeBufferPropertiesOHOS(device,buffer,&props);
 printf("BLOB_PROPERTIES result=%d format=%d features=%x size=%llu\n",query,fmt.format,fmt.formatFeatures,(unsigned long long)props.allocationSize);
 CHECK(query==VK_SUCCESS&&fmt.format==VK_FORMAT_UNDEFINED&&fmt.formatFeatures==0&&fmt.externalFormat==0);
 VkImportNativeBufferInfoOHOS imported{VK_STRUCTURE_TYPE_IMPORT_NATIVE_BUFFER_INFO_OHOS};imported.buffer=buffer;
 VkMemoryDedicatedAllocateInfo dedicated{VK_STRUCTURE_TYPE_MEMORY_DEDICATED_ALLOCATE_INFO};dedicated.pNext=&imported;dedicated.buffer=source;
 VkMemoryAllocateInfo alloc{VK_STRUCTURE_TYPE_MEMORY_ALLOCATE_INFO};alloc.pNext=&dedicated;alloc.allocationSize=req.size;alloc.memoryTypeIndex=__builtin_ctz(props.memoryTypeBits&req.memoryTypeBits);
 VkDeviceMemory sourceMemory;
 auto invalid=[&](){VkDeviceMemory rejected=VK_NULL_HANDLE;CHECK(vkAllocateMemory(device,&alloc,nullptr,&rejected)==VK_ERROR_INVALID_EXTERNAL_HANDLE);CHECK(rejected==VK_NULL_HANDLE);};
 alloc.allocationSize=logical-1;invalid();alloc.allocationSize=h->size+64;invalid();alloc.allocationSize=req.size;
 h->usage|=1ULL<<11;invalid();h->usage&=~(1ULL<<11);
 h->height=2;invalid();h->height=1;
 h->format=999;invalid();h->format=38;
 h->size=4096;invalid();h->size=20480;
 VKCHECK(vkAllocateMemory(device,&alloc,nullptr,&sourceMemory));VKCHECK(vkBindBufferMemory(device,source,sourceMemory,0));
 puts("BLOB_INVALID_REJECTED=6");
 bi.pNext=nullptr;bi.size=logical+guards;bi.usage=VK_BUFFER_USAGE_TRANSFER_DST_BIT;
 VkBuffer destination;VKCHECK(vkCreateBuffer(device,&bi,nullptr,&destination));vkGetBufferMemoryRequirements(device,destination,&req);
 VkPhysicalDeviceMemoryProperties mp;vkGetPhysicalDeviceMemoryProperties(physical,&mp);unsigned hostType=mp.memoryTypeCount;
 for(unsigned i=0;i<mp.memoryTypeCount;i++)if((req.memoryTypeBits&(1u<<i))&&
   (mp.memoryTypes[i].propertyFlags&(VK_MEMORY_PROPERTY_HOST_VISIBLE_BIT|VK_MEMORY_PROPERTY_HOST_COHERENT_BIT))==(VK_MEMORY_PROPERTY_HOST_VISIBLE_BIT|VK_MEMORY_PROPERTY_HOST_COHERENT_BIT)){hostType=i;break;}
 CHECK(hostType<mp.memoryTypeCount);alloc.pNext=nullptr;alloc.allocationSize=req.size;alloc.memoryTypeIndex=hostType;
 VkDeviceMemory destinationMemory;VKCHECK(vkAllocateMemory(device,&alloc,nullptr,&destinationMemory));VKCHECK(vkBindBufferMemory(device,destination,destinationMemory,0));
 void *mapping=nullptr;VKCHECK(vkMapMemory(device,destinationMemory,0,VK_WHOLE_SIZE,0,&mapping));std::memset(mapping,0xcd,logical+guards);
 VkCommandPoolCreateInfo pci{VK_STRUCTURE_TYPE_COMMAND_POOL_CREATE_INFO};VkCommandPool pool;VKCHECK(vkCreateCommandPool(device,&pci,nullptr,&pool));
 VkCommandBufferAllocateInfo cai{VK_STRUCTURE_TYPE_COMMAND_BUFFER_ALLOCATE_INFO};cai.commandPool=pool;cai.level=VK_COMMAND_BUFFER_LEVEL_PRIMARY;cai.commandBufferCount=1;
 VkCommandBuffer command;VKCHECK(vkAllocateCommandBuffers(device,&cai,&command));VkCommandBufferBeginInfo cbi{VK_STRUCTURE_TYPE_COMMAND_BUFFER_BEGIN_INFO};VKCHECK(vkBeginCommandBuffer(command,&cbi));
 VkBufferCopy copy{0,0,logical};vkCmdCopyBuffer(command,source,destination,1,&copy);
 VkMemoryBarrier barrier{VK_STRUCTURE_TYPE_MEMORY_BARRIER};barrier.srcAccessMask=VK_ACCESS_TRANSFER_WRITE_BIT;barrier.dstAccessMask=VK_ACCESS_HOST_READ_BIT;
 vkCmdPipelineBarrier(command,VK_PIPELINE_STAGE_TRANSFER_BIT,VK_PIPELINE_STAGE_HOST_BIT,0,1,&barrier,0,nullptr,0,nullptr);VKCHECK(vkEndCommandBuffer(command));
 VkQueue queue;vkGetDeviceQueue(device,0,0,&queue);VkSubmitInfo submit{VK_STRUCTURE_TYPE_SUBMIT_INFO};submit.commandBufferCount=1;submit.pCommandBuffers=&command;
 VKCHECK(vkQueueSubmit(queue,1,&submit,VK_NULL_HANDLE));VKCHECK(vkQueueWaitIdle(queue));
 auto actual=static_cast<unsigned char*>(mapping);
 for(unsigned i=0;i<logical;i++)CHECK(actual[i]==((i*37+19)&255));
 for(unsigned i=logical;i<logical+guards;i++)CHECK(actual[i]==0xcd);
 vkUnmapMemory(device,destinationMemory);vkDestroyCommandPool(device,pool,nullptr);
 vkDestroyBuffer(device,source,nullptr);vkDestroyBuffer(device,destination,nullptr);
 vkFreeMemory(device,sourceMemory,nullptr);vkFreeMemory(device,destinationMemory,nullptr);
 vkDestroyDevice(device,nullptr);vkDestroyInstance(instance,nullptr);
 printf("BLOB_IMPORT_GPU_COPY_OK verified_bytes=%u guard_bytes=%u invalid_cases=6\n",logical,guards);_exit(0);
}
