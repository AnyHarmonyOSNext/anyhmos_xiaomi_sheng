// A bounded original-library test: real VDI-backed native buffer, original
// NativeBufferUtils import and Drawing surface. No display or user data edits.
#define VK_USE_PLATFORM_OHOS
#include <vulkan/vulkan.h>
#include "idisplay_buffer_vdi.h"
#include <cstdio>
#include <cstdint>
#include <memory>
#include <string>
#include <vector>
#include <dlfcn.h>
#include <unistd.h>
#include <cstring>
#include <cstdlib>
using namespace OHOS::HDI::Display::Buffer::V1_0;
using Shared = std::shared_ptr<void>;
struct NativeRef { void *p; ~NativeRef() {} };
// The donor constructs a nontrivial object through the hidden return pointer.
// Opaque storage is deliberately larger; use its own accessor for the layout.
struct Backend { alignas(16) unsigned char storage[256]{}; ~Backend() {} };
struct ImageInfo { int width, height, color, alpha; Shared colorSpace; };
template<class T> T Field(const void* p, size_t offset) {
    T value{}; std::memcpy(&value, static_cast<const char*>(p)+offset, sizeof(value)); return value;
}
#define CHECK(x) do { if (!(x)) { printf("FAIL line=%d %s error=%s\n",__LINE__,#x,dlerror()); _exit(1); } } while(0)
int main(int argc, char** argv) {
    setbuf(stdout,nullptr); alarm(25); CHECK(argc==2);
    void* lib=dlopen(argv[1],RTLD_NOW|RTLD_GLOBAL); CHECK(lib);
    auto singleton=(void*(*)(const std::string&))dlsym(lib,"_ZN4OHOS5Rosen15RsVulkanContext12GetSingletonERKNSt3__h12basic_stringIcNS2_11char_traitsIcEENS2_9allocatorIcEEEE");
    auto context=(Shared(*)(void*,const std::string&))dlsym(lib,"_ZN4OHOS5Rosen15RsVulkanContext17GetDrawingContextERKNSt3__h12basic_stringIcNS2_11char_traitsIcEENS2_9allocatorIcEEEE");
    // Optional diagnostic smoke test uses the actual preloaded ABI trampoline.
    auto backend=(Backend(*)(void*,int,int,bool))dlsym(std::getenv("SHENG_OBSERVE_IMPORT") ? RTLD_DEFAULT : lib,"_ZN4OHOS5Rosen17NativeBufferUtils34MakeBackendTextureFromNativeBufferEP18NativeWindowBufferiib");
    auto texture=(const void*(*)(const void*))dlsym(lib,"_ZNK4OHOS5Rosen7Drawing14BackendTexture14GetTextureInfoEv");
    auto surface=(Shared(*)(void*,const void*,uint32_t,int,uint32_t,Shared,void(*)(void*),void*))dlsym(lib,"_ZN4OHOS5Rosen7Drawing7Surface22MakeFromBackendTextureEPNS1_10GPUContextERKNS1_11TextureInfoENS1_13TextureOriginEiNS1_9ColorTypeENSt3__h10shared_ptrINS1_10ColorSpaceEEEPFvPvESE_");
    auto canvas=(Shared(*)(void*))dlsym(lib,"_ZN4OHOS5Rosen7Drawing7Surface9GetCanvasEv");
    auto clear=(void(*)(void*,uint32_t))dlsym(lib,"_ZN4OHOS5Rosen7Drawing10CoreCanvas5ClearEj");
    auto read=(bool(*)(void*,const ImageInfo&,void*,size_t,int,int))dlsym(lib,"_ZN4OHOS5Rosen7Drawing10CoreCanvas10ReadPixelsERKNS1_9ImageInfoEPvmii");
    // Resolve the exact spelling independently, as the donor uses EPvmii.
    if (!read) read=(bool(*)(void*,const ImageInfo&,void*,size_t,int,int))dlsym(lib,"_ZN4OHOS5Rosen7Drawing10CoreCanvas10ReadPixelsERKNS1_9ImageInfoEPvmii");
    auto drawing=(int*)dlsym(lib,"_ZN4OHOS5Rosen7Drawing16SystemProperties17systemGpuApiType_E");
    auto rosen=(int*)dlsym(lib,"_ZN4OHOS5Rosen18RSSystemProperties17systemGpuApiType_E");
    CHECK(singleton&&context&&backend&&texture&&surface&&canvas&&clear&&read&&drawing&&rosen);
    *drawing=1; *rosen=1;
    auto* native=dlopen("libnative_buffer.so",RTLD_NOW|RTLD_GLOBAL); CHECK(native);
    auto createNative=(NativeRef(*)())dlsym(native,"_ZN4OHOS13SurfaceBuffer6CreateEv"); CHECK(createNative);
    auto windowLib=dlopen("libnative_window.so",RTLD_NOW|RTLD_GLOBAL); CHECK(windowLib);
    auto wrap=(void*(*)(OH_NativeBuffer*))dlsym(windowLib,"OH_NativeWindow_CreateNativeWindowBufferFromNativeBuffer"); CHECK(wrap);
    auto vdilib=dlopen("/compat/lib64/libdisplay_buffer_vdi_impl.z.so",RTLD_NOW|RTLD_LOCAL); CHECK(vdilib);
    auto create=(CreateDisplayBufferVdiFunc)dlsym(vdilib,"CreateDisplayBufferVdi"); CHECK(create);
    auto vdi=create(); CHECK(vdi); BufferHandle* handle=nullptr;
    CHECK(vdi->AllocMem({842,210,0xc00002b,12,0},handle)==0&&handle);
    auto owner=createNative(); CHECK(owner.p);
    auto** handleField=reinterpret_cast<BufferHandle**>((char*)owner.p+16); CHECK(!*handleField); *handleField=handle;
    void* window=wrap((OH_NativeBuffer*)owner.p); CHECK(window);
    std::string cache; void* rs=singleton(cache); CHECK(rs); auto gpu=context(rs,cache); CHECK(gpu);
    auto imported=backend(window,842,210,false); const void* info=texture(&imported); CHECK(info);
    auto vk=Field<const void*>(info,24); CHECK(vk);
    printf("IMPORTED size=%dx%d stride=%d allocation=%d usage=%x\n",Field<int>(info,0),Field<int>(info,4),handle->stride,handle->size,Field<uint32_t>(vk,76));
    auto target=surface(gpu.get(),info,0,1,4,{},nullptr,nullptr);
    printf("WRAP surface=%p\n",target.get()); if(!target) _exit(3);
    auto c=canvas(target.get()); CHECK(c); clear(c.get(),0xff00ff00);
    ImageInfo pixelInfo{842,210,4,2,{}};
    std::vector<uint32_t> pixels(842*210+32,0x13579bdf);
    CHECK(read(c.get(),pixelInfo,pixels.data(),842*4,0,0));
    for(int n=0;n<842*210;n++) CHECK(pixels[n]==0xff00ff00);
    for(int n=842*210;n<(int)pixels.size();n++) CHECK(pixels[n]==0x13579bdf);
    if (std::getenv("SHENG_GPU_RECLAIM_TEST")) {
        auto reclaim = reinterpret_cast<void (*)(void*)>(dlsym(RTLD_DEFAULT, "ShengReclaimContext"));
        CHECK(reclaim); reclaim(gpu.get());
        CHECK(read(c.get(),pixelInfo,pixels.data(),842*4,0,0));
        for(int n=0;n<842*210;n++) CHECK(pixels[n]==0xff00ff00);
        for(int n=842*210;n<(int)pixels.size();n++) CHECK(pixels[n]==0x13579bdf);
        printf("SURFACE_RECLAIM_OK content_and_guards_preserved=1\n");
    }
    printf("SURFACE_USAGE_OK original_import=1 original_surface=1 rgba_pixels=%d guard_words=32\n",842*210);
    _exit(0);
}
