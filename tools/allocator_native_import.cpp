// Original SurfaceBuffer fixture with handles allocated by the real VDI.
// This tests DMA-BUF/Vulkan import, not producer or allocator Binder IPC.
#define VK_USE_PLATFORM_OHOS
#include <vulkan/vulkan.h>
#include "idisplay_buffer_vdi.h"
#include <cstdio>
#include <dlfcn.h>
#include <unistd.h>
using namespace OHOS::HDI::Display::Buffer::V1_0;
struct NativeRef { void *p; ~NativeRef() {} };
#define CHECK(x) do { if (!(x)) { printf("FAIL line=%d %s\n", __LINE__, #x); return 1; } } while (0)
#define VKCHECK(x) do { VkResult v=(x); if(v) { printf("FAIL line=%d result=%d %s\n",__LINE__,v,#x); return 2; } } while(0)
#define INST(n) auto n=(PFN_##n)gipa(instance,#n); CHECK(n)
#define DEV(n) auto n=(PFN_##n)vkGetDeviceProcAddr(device,#n); CHECK(n)
int main(int argc,char **argv)
{
    setbuf(stdout,nullptr); alarm(25); CHECK(argc==3);
    auto *native=dlopen("libnative_buffer.so",RTLD_NOW|RTLD_GLOBAL); CHECK(native);
    auto createNative=(NativeRef(*)())dlsym(native,"_ZN4OHOS13SurfaceBuffer6CreateEv");
    auto unref=(int(*)(OH_NativeBuffer*))dlsym(native,"OH_NativeBuffer_Unreference");
    auto getHandle=(const BufferHandle*(*)(const OH_NativeBuffer*))dlsym(native,"OH_NativeBuffer_GetBufferHandle");
    CHECK(createNative&&unref&&getHandle);
    void *vdiSo=dlopen(argv[1],RTLD_NOW|RTLD_LOCAL); CHECK(vdiSo);
    auto create=(CreateDisplayBufferVdiFunc)dlsym(vdiSo,"CreateDisplayBufferVdi");
    auto destroy=(DestroyDisplayBufferVdiFunc)dlsym(vdiSo,"DestroyDisplayBufferVdi"); CHECK(create&&destroy);
    auto *vdi=create(); CHECK(vdi);
    auto *driver=dlopen(argv[2],RTLD_NOW|RTLD_LOCAL); CHECK(driver);
    auto gipa=(PFN_vkGetInstanceProcAddr)dlsym(driver,"vk_icdGetInstanceProcAddr"); CHECK(gipa);
    VkInstance instance=VK_NULL_HANDLE; INST(vkCreateInstance);
    VkApplicationInfo app{VK_STRUCTURE_TYPE_APPLICATION_INFO}; app.apiVersion=VK_API_VERSION_1_1;
    VkInstanceCreateInfo ici{VK_STRUCTURE_TYPE_INSTANCE_CREATE_INFO}; ici.pApplicationInfo=&app;
    VKCHECK(vkCreateInstance(&ici,nullptr,&instance));
    INST(vkEnumeratePhysicalDevices); INST(vkCreateDevice); INST(vkGetDeviceProcAddr); INST(vkDestroyInstance);
    uint32_t count=1; VkPhysicalDevice physical; VKCHECK(vkEnumeratePhysicalDevices(instance,&count,&physical));
    float priority=1; VkDeviceQueueCreateInfo q{VK_STRUCTURE_TYPE_DEVICE_QUEUE_CREATE_INFO};
    q.queueCount=1; q.pQueuePriorities=&priority;
    const char *extensions[]={"VK_OHOS_external_memory","VK_OHOS_native_buffer"};
    VkDeviceCreateInfo dc{VK_STRUCTURE_TYPE_DEVICE_CREATE_INFO}; dc.queueCreateInfoCount=1; dc.pQueueCreateInfos=&q;
    dc.enabledExtensionCount=2; dc.ppEnabledExtensionNames=extensions;
    VkDevice device; VKCHECK(vkCreateDevice(physical,&dc,nullptr,&device));
    DEV(vkGetNativeBufferPropertiesOHOS); DEV(vkCreateImage); DEV(vkAllocateMemory); DEV(vkBindImageMemory2);
    DEV(vkDestroyImage); DEV(vkFreeMemory); DEV(vkDestroyDevice);
    for(auto dims : {std::pair<uint32_t,uint32_t>{1512,1008},{136,136},{325,323},{3048,2032}}) {
        BufferHandle *h=nullptr;
        CHECK(vdi->AllocMem({dims.first,dims.second,0xc00002b,12,0},h)==0&&h);
        printf("ALLOC_IMPORT width=%u height=%u stride=%d size=%d\n",dims.first,dims.second,h->stride,h->size);
        auto owner=createNative(); CHECK(owner.p);
        auto **field=reinterpret_cast<BufferHandle**>((char*)owner.p+16); CHECK(*field==nullptr); *field=h;
        auto *buffer=(OH_NativeBuffer*)owner.p; CHECK(getHandle(buffer)==h);
        VkNativeBufferFormatPropertiesOHOS fp{VK_STRUCTURE_TYPE_NATIVE_BUFFER_FORMAT_PROPERTIES_OHOS};
        VkNativeBufferPropertiesOHOS bp{VK_STRUCTURE_TYPE_NATIVE_BUFFER_PROPERTIES_OHOS}; bp.pNext=&fp;
        VKCHECK(vkGetNativeBufferPropertiesOHOS(device,buffer,&bp)); CHECK(bp.memoryTypeBits);
        VkExternalMemoryImageCreateInfo external{VK_STRUCTURE_TYPE_EXTERNAL_MEMORY_IMAGE_CREATE_INFO};
        external.handleTypes=VK_EXTERNAL_MEMORY_HANDLE_TYPE_OHOS_NATIVE_BUFFER_BIT_OHOS;
        VkImageCreateInfo imageInfo{VK_STRUCTURE_TYPE_IMAGE_CREATE_INFO}; imageInfo.pNext=&external;
        imageInfo.imageType=VK_IMAGE_TYPE_2D; imageInfo.format=fp.format;
        imageInfo.extent={dims.first,dims.second,1}; imageInfo.mipLevels=1; imageInfo.arrayLayers=1;
        imageInfo.samples=VK_SAMPLE_COUNT_1_BIT; imageInfo.tiling=VK_IMAGE_TILING_OPTIMAL;
        imageInfo.usage=VK_IMAGE_USAGE_SAMPLED_BIT|VK_IMAGE_USAGE_COLOR_ATTACHMENT_BIT;
        VkImage image; VKCHECK(vkCreateImage(device,&imageInfo,nullptr,&image));
        VkImportNativeBufferInfoOHOS import{VK_STRUCTURE_TYPE_IMPORT_NATIVE_BUFFER_INFO_OHOS}; import.buffer=buffer;
        VkMemoryDedicatedAllocateInfo dedicated{VK_STRUCTURE_TYPE_MEMORY_DEDICATED_ALLOCATE_INFO};
        dedicated.pNext=&import; dedicated.image=image;
        VkMemoryAllocateInfo alloc{VK_STRUCTURE_TYPE_MEMORY_ALLOCATE_INFO}; alloc.pNext=&dedicated;
        alloc.allocationSize=bp.allocationSize; alloc.memoryTypeIndex=__builtin_ctz(bp.memoryTypeBits);
        VkDeviceMemory memory; VKCHECK(vkAllocateMemory(device,&alloc,nullptr,&memory));
        VkBindImageMemoryInfo bind{VK_STRUCTURE_TYPE_BIND_IMAGE_MEMORY_INFO}; bind.image=image; bind.memory=memory;
        VKCHECK(vkBindImageMemory2(device,1,&bind));
        vkDestroyImage(device,image,nullptr); vkFreeMemory(device,memory,nullptr);
        *field=nullptr; CHECK(unref(buffer)==0); vdi->FreeMem(*h);
    }
    vkDestroyDevice(device,nullptr); vkDestroyInstance(instance,nullptr); destroy(vdi);
    puts("ALLOCATOR_NATIVE_IMPORT_OK cases=4 original_surfacebuffer=1 handle_field_fixture=1 no_drm_master=1");
    return 0;
}
