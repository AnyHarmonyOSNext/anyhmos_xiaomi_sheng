// Execute real shaders into an original OHOS SurfaceBuffer object.
// Recovery has no HDI service. Install the separately tested DMA handle at
// pinned ROM offset16; this fixture does not validate producer/allocator IPC.
#define VK_USE_PLATFORM_OHOS
#include <vulkan/vulkan.h>
#include <dlfcn.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>
#include <fcntl.h>
#include <poll.h>
#include <sys/mman.h>
#include <sys/ioctl.h>
#include <linux/dma-buf.h>
#include <linux/dma-heap.h>


struct Handle {int32_t fd,width,stride,height,size,format;uint64_t usage;void *virAddr;uint64_t phyAddr;uint32_t reserveFds,reserveInts;};
// Nontrivial result preserves the original sptr return ABI. Release through NDK.
struct NativeRef {void *p;~NativeRef(){}};
#define CHECK(x) do{if(!(x)){printf("FAIL line=%d %s\n",__LINE__,#x);return 1;}}while(0)
#define VKCHECK(x) do{VkResult r=(x);if(r!=VK_SUCCESS){printf("FAIL line=%d result=%d %s\n",__LINE__,r,#x);return 1;}}while(0)
#define INST(n) auto n=(PFN_##n)gipa(instance,#n);CHECK(n)
#define DEV(n) auto n=(PFN_##n)vkGetDeviceProcAddr(device,#n);CHECK(n)
int main(int argc,char**argv){
 setbuf(stdout,NULL);alarm(30);CHECK(argc==2||argc==3);
 puts("BEFORE_NATIVE_LOAD");void *native=dlopen("libnative_buffer.so",RTLD_NOW|RTLD_GLOBAL);if(!native){puts(dlerror());return 1;}
 auto create=(NativeRef(*)())dlsym(native,"_ZN4OHOS13SurfaceBuffer6CreateEv");
 auto set=(void(*)(void*,Handle*))dlsym(native,"_ZN4OHOS17SurfaceBufferImpl15SetBufferHandleEP12BufferHandle");
 auto get=(const Handle*(*)(const OH_NativeBuffer*))dlsym(native,"OH_NativeBuffer_GetBufferHandle");
 auto unref=(int(*)(OH_NativeBuffer*))dlsym(native,"OH_NativeBuffer_Unreference");CHECK(create&&set&&get&&unref);
 constexpr int W=3048,H=2032,logical=12288*H;int total=argc==3?12288*2048:logical;printf("LAYOUT_PROBE w=%d h=%d stride=12288 size=%d padded=%d\n",W,H,total,argc==3);
 int heap=open("/dev/dma_heap/system",O_RDONLY|O_CLOEXEC);CHECK(heap>=0);
 dma_heap_allocation_data req{};req.len=total;req.fd_flags=O_RDWR|O_CLOEXEC;CHECK(ioctl(heap,DMA_HEAP_IOCTL_ALLOC,&req)==0);close(heap);
 auto *h=(Handle*)calloc(1,sizeof(Handle));h->fd=req.fd;h->width=W;h->height=H;h->stride=12288;h->size=total;h->format=12;h->usage=0x708;
 auto *pixels=(uint8_t*)mmap(NULL,total,PROT_READ|PROT_WRITE,MAP_SHARED,h->fd,0);CHECK(pixels!=MAP_FAILED);
 dma_buf_sync sync{DMA_BUF_SYNC_START|DMA_BUF_SYNC_RW};CHECK(ioctl(h->fd,DMA_BUF_IOCTL_SYNC,&sync)==0);memset(pixels,0xcd,total);sync.flags=DMA_BUF_SYNC_END|DMA_BUF_SYNC_RW;CHECK(ioctl(h->fd,DMA_BUF_IOCTL_SYNC,&sync)==0);
 puts("BEFORE_NATIVE_CREATE");auto owner=create();puts("AFTER_NATIVE_CREATE");CHECK(owner.p);CHECK(*reinterpret_cast<Handle**>((char*)owner.p+16)==nullptr);*reinterpret_cast<Handle**>((char*)owner.p+16)=h;auto *buffer=(OH_NativeBuffer*)owner.p;CHECK(get(buffer)&&get(buffer)->fd==h->fd);
 puts("ORIGINAL_NATIVE_BUFFER_CREATED=1");
 puts("BEFORE_DRIVER_LOAD");void *lib=dlopen(argv[1],RTLD_NOW|RTLD_LOCAL);if(!lib){puts(dlerror());return 1;}
 auto gipa=(PFN_vkGetInstanceProcAddr)dlsym(lib,"vk_icdGetInstanceProcAddr");if(!gipa)gipa=(PFN_vkGetInstanceProcAddr)dlsym(lib,"vkGetInstanceProcAddr");CHECK(gipa);VkInstance instance=VK_NULL_HANDLE;
 INST(vkCreateInstance);VkApplicationInfo app{VK_STRUCTURE_TYPE_APPLICATION_INFO};app.apiVersion=VK_API_VERSION_1_1;
 VkInstanceCreateInfo ici{VK_STRUCTURE_TYPE_INSTANCE_CREATE_INFO};ici.pApplicationInfo=&app;puts("BEFORE_INSTANCE");VKCHECK(vkCreateInstance(&ici,NULL,&instance));puts("AFTER_INSTANCE");
 INST(vkEnumeratePhysicalDevices);INST(vkGetPhysicalDeviceProperties);INST(vkCreateDevice);INST(vkGetDeviceProcAddr);INST(vkDestroyInstance);
 uint32_t count=1;VkPhysicalDevice physical;VKCHECK(vkEnumeratePhysicalDevices(instance,&count,&physical));CHECK(count);
 VkPhysicalDeviceProperties prop;vkGetPhysicalDeviceProperties(physical,&prop);printf("GPU=%s\n",prop.deviceName);
 float priority=1;VkDeviceQueueCreateInfo qci{VK_STRUCTURE_TYPE_DEVICE_QUEUE_CREATE_INFO};qci.queueFamilyIndex=0;qci.queueCount=1;qci.pQueuePriorities=&priority;
 const char*exts[]={"VK_OHOS_external_memory","VK_OHOS_native_buffer","VK_KHR_external_semaphore_fd","VK_KHR_external_fence_fd"};
 VkDeviceCreateInfo dci{VK_STRUCTURE_TYPE_DEVICE_CREATE_INFO};dci.queueCreateInfoCount=1;dci.pQueueCreateInfos=&qci;dci.enabledExtensionCount=4;dci.ppEnabledExtensionNames=exts;
 #ifdef ACE5_YUV_CONTRACT
 VkPhysicalDeviceSamplerYcbcrConversionFeatures yuvFeatures{VK_STRUCTURE_TYPE_PHYSICAL_DEVICE_SAMPLER_YCBCR_CONVERSION_FEATURES};yuvFeatures.samplerYcbcrConversion=VK_TRUE;dci.pNext=&yuvFeatures;
#endif
 VkDevice device;puts("BEFORE_DEVICE");VKCHECK(vkCreateDevice(physical,&dci,NULL,&device));puts("AFTER_DEVICE");
 DEV(vkGetNativeBufferPropertiesOHOS);DEV(vkGetMemoryNativeBufferOHOS);DEV(vkAcquireImageOHOS);DEV(vkQueueSignalReleaseImageOHOS);
 DEV(vkCreateImage);DEV(vkAllocateMemory);DEV(vkBindImageMemory2);DEV(vkCreateImageView);DEV(vkCreateRenderPass);DEV(vkCreateFramebuffer);
 DEV(vkCreateShaderModule);DEV(vkCreatePipelineLayout);DEV(vkCreateGraphicsPipelines);DEV(vkGetDeviceQueue);
 DEV(vkCreateCommandPool);DEV(vkAllocateCommandBuffers);DEV(vkBeginCommandBuffer);DEV(vkCmdBeginRenderPass);DEV(vkCmdBindPipeline);DEV(vkCmdDraw);DEV(vkCmdEndRenderPass);DEV(vkCmdPipelineBarrier);DEV(vkEndCommandBuffer);DEV(vkQueueSubmit);DEV(vkQueueWaitIdle);DEV(vkCreateSemaphore);
 DEV(vkDestroyImage);DEV(vkFreeMemory);DEV(vkDestroySemaphore);DEV(vkDestroyPipeline);DEV(vkDestroyPipelineLayout);DEV(vkDestroyShaderModule);DEV(vkDestroyFramebuffer);DEV(vkDestroyRenderPass);DEV(vkDestroyImageView);DEV(vkDestroyCommandPool);DEV(vkDestroyDevice);

#ifdef ACE5_YUV_CONTRACT
 DEV(vkCreateSamplerYcbcrConversion);DEV(vkDestroySamplerYcbcrConversion);DEV(vkCreateSampler);DEV(vkDestroySampler);DEV(vkCreateDescriptorSetLayout);DEV(vkDestroyDescriptorSetLayout);DEV(vkCreateDescriptorPool);DEV(vkDestroyDescriptorPool);DEV(vkAllocateDescriptorSets);DEV(vkUpdateDescriptorSets);DEV(vkCmdBindDescriptorSets);
 constexpr int yLogical=W*H*3/2,yTotal=yLogical+4096;
 int yh=open("/dev/dma_heap/system",O_RDONLY|O_CLOEXEC);CHECK(yh>=0);dma_heap_allocation_data yr{};yr.len=yTotal;yr.fd_flags=O_RDWR|O_CLOEXEC;CHECK(!ioctl(yh,DMA_HEAP_IOCTL_ALLOC,&yr));close(yh);
 auto *yHandle=(Handle*)calloc(1,sizeof(Handle));yHandle->fd=yr.fd;yHandle->width=W;yHandle->height=H;yHandle->stride=W;yHandle->size=yTotal;yHandle->format=24;yHandle->usage=0x42b;
 auto *yPixels=(uint8_t*)mmap(NULL,yTotal,PROT_READ|PROT_WRITE,MAP_SHARED,yr.fd,0);CHECK(yPixels!=MAP_FAILED);dma_buf_sync ys{DMA_BUF_SYNC_START|DMA_BUF_SYNC_RW};CHECK(!ioctl(yr.fd,DMA_BUF_IOCTL_SYNC,&ys));
 memset(yPixels,0xcd,yTotal);
 // Three vertical BT.601 limited-range bands: red, green, blue. This catches
 // wrong UV offset, swapped components and incorrect YCbCr conversion.
 const unsigned char yuv[3][3]={{81,90,240},{145,54,34},{41,240,110}};
 for(int y=0;y<H;y++)for(int x=0;x<W;x++)yPixels[y*W+x]=yuv[x<42?0:x<84?1:2][0];
 for(int y=0;y<H/2;y++)for(int x=0;x<W;x+=2){int band=x<42?0:x<84?1:2;yPixels[W*H+y*W+x]=yuv[band][1];yPixels[W*H+y*W+x+1]=yuv[band][2];}
 ys.flags=DMA_BUF_SYNC_END|DMA_BUF_SYNC_RW;CHECK(!ioctl(yr.fd,DMA_BUF_IOCTL_SYNC,&ys));auto yOwner=create();CHECK(yOwner.p);CHECK(!*reinterpret_cast<Handle**>((char*)yOwner.p+16));*reinterpret_cast<Handle**>((char*)yOwner.p+16)=yHandle;auto*yBuffer=(OH_NativeBuffer*)yOwner.p;
 VkNativeBufferFormatPropertiesOHOS yf{VK_STRUCTURE_TYPE_NATIVE_BUFFER_FORMAT_PROPERTIES_OHOS};VkNativeBufferPropertiesOHOS yp{VK_STRUCTURE_TYPE_NATIVE_BUFFER_PROPERTIES_OHOS};yp.pNext=&yf;VKCHECK(vkGetNativeBufferPropertiesOHOS(device,yBuffer,&yp));CHECK(yf.format==VK_FORMAT_UNDEFINED && yf.externalFormat==24);CHECK(yp.allocationSize==yTotal);
 VkExternalFormatOHOS yext{VK_STRUCTURE_TYPE_EXTERNAL_FORMAT_OHOS};yext.externalFormat=yf.externalFormat;
 VkExternalMemoryImageCreateInfo ye{VK_STRUCTURE_TYPE_EXTERNAL_MEMORY_IMAGE_CREATE_INFO};ye.pNext=&yext;ye.handleTypes=VK_EXTERNAL_MEMORY_HANDLE_TYPE_OHOS_NATIVE_BUFFER_BIT_OHOS;VkImageCreateInfo yi{VK_STRUCTURE_TYPE_IMAGE_CREATE_INFO};yi.pNext=&ye;yi.imageType=VK_IMAGE_TYPE_2D;yi.format=yf.format;yi.extent={W,H,1};yi.mipLevels=yi.arrayLayers=1;yi.samples=VK_SAMPLE_COUNT_1_BIT;yi.tiling=VK_IMAGE_TILING_OPTIMAL;yi.usage=VK_IMAGE_USAGE_SAMPLED_BIT;yi.initialLayout=VK_IMAGE_LAYOUT_PREINITIALIZED;VkImage yImage; yext.externalFormat=999; CHECK(vkCreateImage(device,&yi,NULL,&yImage)==VK_ERROR_FORMAT_NOT_SUPPORTED);yext.externalFormat=yf.externalFormat;VKCHECK(vkCreateImage(device,&yi,NULL,&yImage));
 VkImportNativeBufferInfoOHOS yimp{VK_STRUCTURE_TYPE_IMPORT_NATIVE_BUFFER_INFO_OHOS};yimp.buffer=yBuffer;VkMemoryDedicatedAllocateInfo yd{VK_STRUCTURE_TYPE_MEMORY_DEDICATED_ALLOCATE_INFO};yd.pNext=&yimp;yd.image=yImage;VkMemoryAllocateInfo ya{VK_STRUCTURE_TYPE_MEMORY_ALLOCATE_INFO};ya.pNext=&yd;ya.allocationSize=yp.allocationSize;ya.memoryTypeIndex=__builtin_ctz(yp.memoryTypeBits);VkDeviceMemory yMemory;VKCHECK(vkAllocateMemory(device,&ya,NULL,&yMemory));VKCHECK(vkBindImageMemory(device,yImage,yMemory,0));
 VkSamplerYcbcrConversionCreateInfo yc{VK_STRUCTURE_TYPE_SAMPLER_YCBCR_CONVERSION_CREATE_INFO};yc.pNext=&yext;yc.format=yf.format;yc.ycbcrModel=yf.suggestedYcbcrModel;yc.ycbcrRange=yf.suggestedYcbcrRange;yc.components=yf.samplerYcbcrConversionComponents;yc.xChromaOffset=yf.suggestedXChromaOffset;yc.yChromaOffset=yf.suggestedYChromaOffset;yc.chromaFilter=VK_FILTER_NEAREST;VkSamplerYcbcrConversion conversion;yext.externalFormat=999;CHECK(vkCreateSamplerYcbcrConversion(device,&yc,NULL,&conversion)==VK_ERROR_FORMAT_NOT_SUPPORTED);yext.externalFormat=yf.externalFormat;VKCHECK(vkCreateSamplerYcbcrConversion(device,&yc,NULL,&conversion));
 VkSamplerYcbcrConversionInfo yci{VK_STRUCTURE_TYPE_SAMPLER_YCBCR_CONVERSION_INFO};yci.conversion=conversion;VkSamplerCreateInfo sci{VK_STRUCTURE_TYPE_SAMPLER_CREATE_INFO};sci.pNext=&yci;sci.magFilter=sci.minFilter=VK_FILTER_NEAREST;sci.mipmapMode=VK_SAMPLER_MIPMAP_MODE_NEAREST;sci.addressModeU=sci.addressModeV=sci.addressModeW=VK_SAMPLER_ADDRESS_MODE_CLAMP_TO_EDGE;VkSampler sampler;VKCHECK(vkCreateSampler(device,&sci,NULL,&sampler));
 VkImageViewCreateInfo yvi{VK_STRUCTURE_TYPE_IMAGE_VIEW_CREATE_INFO};yvi.pNext=&yci;yvi.image=yImage;yvi.viewType=VK_IMAGE_VIEW_TYPE_2D;yvi.format=yf.format;yvi.subresourceRange={VK_IMAGE_ASPECT_COLOR_BIT,0,1,0,1};VkImageView yView;VKCHECK(vkCreateImageView(device,&yvi,NULL,&yView));
 VkDescriptorSetLayoutBinding binding{};binding.binding=0;binding.descriptorType=VK_DESCRIPTOR_TYPE_COMBINED_IMAGE_SAMPLER;binding.descriptorCount=1;binding.stageFlags=VK_SHADER_STAGE_FRAGMENT_BIT;binding.pImmutableSamplers=&sampler;VkDescriptorSetLayoutCreateInfo dl{VK_STRUCTURE_TYPE_DESCRIPTOR_SET_LAYOUT_CREATE_INFO};dl.bindingCount=1;dl.pBindings=&binding;VkDescriptorSetLayout setLayout;VKCHECK(vkCreateDescriptorSetLayout(device,&dl,NULL,&setLayout));
 VkDescriptorPoolSize poolSize{VK_DESCRIPTOR_TYPE_COMBINED_IMAGE_SAMPLER,8};VkDescriptorPoolCreateInfo dp{VK_STRUCTURE_TYPE_DESCRIPTOR_POOL_CREATE_INFO};dp.maxSets=1;dp.poolSizeCount=1;dp.pPoolSizes=&poolSize;VkDescriptorPool descriptorPool;VKCHECK(vkCreateDescriptorPool(device,&dp,NULL,&descriptorPool));VkDescriptorSetAllocateInfo da{VK_STRUCTURE_TYPE_DESCRIPTOR_SET_ALLOCATE_INFO};da.descriptorPool=descriptorPool;da.descriptorSetCount=1;da.pSetLayouts=&setLayout;VkDescriptorSet descriptorSet;VKCHECK(vkAllocateDescriptorSets(device,&da,&descriptorSet));VkDescriptorImageInfo di{sampler,yView,VK_IMAGE_LAYOUT_SHADER_READ_ONLY_OPTIMAL};VkWriteDescriptorSet wd{VK_STRUCTURE_TYPE_WRITE_DESCRIPTOR_SET};wd.dstSet=descriptorSet;wd.dstBinding=0;wd.descriptorCount=1;wd.descriptorType=VK_DESCRIPTOR_TYPE_COMBINED_IMAGE_SAMPLER;wd.pImageInfo=&di;vkUpdateDescriptorSets(device,1,&wd,0,NULL);
#endif
 VkNativeBufferFormatPropertiesOHOS fp{VK_STRUCTURE_TYPE_NATIVE_BUFFER_FORMAT_PROPERTIES_OHOS};VkNativeBufferPropertiesOHOS bp{VK_STRUCTURE_TYPE_NATIVE_BUFFER_PROPERTIES_OHOS};bp.pNext=&fp;
 VKCHECK(vkGetNativeBufferPropertiesOHOS(device,buffer,&bp));CHECK(fp.format==VK_FORMAT_R8G8B8A8_UNORM&&bp.allocationSize==total&&bp.memoryTypeBits);
 printf("NATIVE_PROPERTIES size=%llu memoryBits=%x format=%d\n",(unsigned long long)bp.allocationSize,bp.memoryTypeBits,fp.format);
 VkExternalMemoryImageCreateInfo ext{VK_STRUCTURE_TYPE_EXTERNAL_MEMORY_IMAGE_CREATE_INFO};ext.handleTypes=VK_EXTERNAL_MEMORY_HANDLE_TYPE_OHOS_NATIVE_BUFFER_BIT_OHOS;
 VkImageCreateInfo imageInfo{VK_STRUCTURE_TYPE_IMAGE_CREATE_INFO};imageInfo.pNext=&ext;imageInfo.imageType=VK_IMAGE_TYPE_2D;imageInfo.format=fp.format;imageInfo.extent={W,H,1};imageInfo.mipLevels=1;imageInfo.arrayLayers=1;imageInfo.samples=VK_SAMPLE_COUNT_1_BIT;imageInfo.tiling=VK_IMAGE_TILING_OPTIMAL;imageInfo.usage=VK_IMAGE_USAGE_COLOR_ATTACHMENT_BIT|VK_IMAGE_USAGE_SAMPLED_BIT;
 VkExternalFormatOHOS externalFormat{VK_STRUCTURE_TYPE_EXTERNAL_FORMAT_OHOS};ext.pNext=&externalFormat;imageInfo.usage|=VK_IMAGE_USAGE_TRANSFER_SRC_BIT|VK_IMAGE_USAGE_TRANSFER_DST_BIT|VK_IMAGE_USAGE_INPUT_ATTACHMENT_BIT;VkImage image;VKCHECK(vkCreateImage(device,&imageInfo,NULL,&image));
 VkImportNativeBufferInfoOHOS import{VK_STRUCTURE_TYPE_IMPORT_NATIVE_BUFFER_INFO_OHOS};import.buffer=buffer;
 VkMemoryDedicatedAllocateInfo ded{VK_STRUCTURE_TYPE_MEMORY_DEDICATED_ALLOCATE_INFO};ded.image=image;ded.pNext=&import;
 VkMemoryAllocateInfo mai{VK_STRUCTURE_TYPE_MEMORY_ALLOCATE_INFO};mai.pNext=&ded;mai.allocationSize=bp.allocationSize;mai.memoryTypeIndex=__builtin_ctz(bp.memoryTypeBits);
 VkDeviceMemory memory;VKCHECK(vkAllocateMemory(device,&mai,NULL,&memory));VkBindImageMemoryInfo bind{VK_STRUCTURE_TYPE_BIND_IMAGE_MEMORY_INFO};bind.image=image;bind.memory=memory;VKCHECK(vkBindImageMemory2(device,1,&bind));
 printf("FULLSIZE_IMPORT_OK stride=%d size=%d\n",h->stride,total);_exit(0);}
