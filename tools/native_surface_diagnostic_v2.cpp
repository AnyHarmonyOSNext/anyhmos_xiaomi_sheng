// Observe the original Drawing factory without changing its return value or GPU mode.
#include <cstdio>
#include <cstdint>
#include <dlfcn.h>
#include <memory>
#include <cstring>
#include <sys/syscall.h>
#include <unistd.h>

using Surface = std::shared_ptr<void>;
using Factory = Surface (*)(void*, const void*, uint32_t, int, uint32_t,
                           std::shared_ptr<void>, void (*)(void*), void*);
struct ImageInfo { int width, height, color, alpha; std::shared_ptr<void> colorSpace; };
template <class T> static T Field(const void* address, size_t offset)
{
    T value{};
    std::memcpy(&value, static_cast<const char*>(address) + offset, sizeof(value));
    return value;
}
Surface ObserveFactory(void*, const void*, uint32_t, int, uint32_t,
                       std::shared_ptr<void>, void (*)(void*), void*)
    asm("_ZN4OHOS5Rosen7Drawing7Surface22MakeFromBackendTextureEPNS1_10GPUContextERKNS1_11TextureInfoENS1_13TextureOriginEiNS1_9ColorTypeENSt3__h10shared_ptrINS1_10ColorSpaceEEEPFvPvESE_");

Surface ObserveFactory(void* gpu, const void* texture, uint32_t origin, int samples,
                       uint32_t color, std::shared_ptr<void> space,
                       void (*cleanup)(void*), void* helper)
{
    static auto original = reinterpret_cast<Factory>(dlsym(RTLD_NEXT,
        "_ZN4OHOS5Rosen7Drawing7Surface22MakeFromBackendTextureEPNS1_10GPUContextERKNS1_11TextureInfoENS1_13TextureOriginEiNS1_9ColorTypeENSt3__h10shared_ptrINS1_10ColorSpaceEEEPFvPvESE_"));
    if (!original) { std::fprintf(stderr, "SHENG_SURFACE_FACTORY_MISSING %s\n", dlerror()); return {}; }
    auto result = original(gpu, texture, origin, samples, color, space, cleanup, helper);
    static unsigned calls = 0, failures = 0;
    unsigned call = __atomic_add_fetch(&calls, 1, __ATOMIC_RELAXED);
    if (call <= 12 || (!result && __atomic_add_fetch(&failures, 1, __ATOMIC_RELAXED) <= 24)) {
        auto drawing = static_cast<int*>(dlsym(RTLD_DEFAULT,
            "_ZN4OHOS5Rosen7Drawing16SystemProperties17systemGpuApiType_E"));
        auto rosen = static_cast<int*>(dlsym(RTLD_DEFAULT,
            "_ZN4OHOS5Rosen18RSSystemProperties17systemGpuApiType_E"));
        Dl_info location{}; dladdr(reinterpret_cast<void*>(original), &location);
        std::fprintf(stderr,
            "SHENG_SURFACE_FACTORY tid=%ld gpu=%p texture=%p origin=%u samples=%d color=%u result=%p drawing=%d rosen=%d original=%s\n",
            syscall(SYS_gettid), gpu, texture, origin, samples, color, result.get(),
            drawing ? *drawing : -1, rosen ? *rosen : -1,
            location.dli_fname ? location.dli_fname : "?");
        // Offsets verified against this donor's ConvertToGrBackendVKTexture
        // implementation (0x195d0c), rather than inferred from another ABI.
        if (texture) {
            auto vk = Field<const void*>(texture, 24);
            std::fprintf(stderr, "SHENG_TEXTURE_V2 size=%dx%d vk=%p\n",
                Field<int>(texture, 0), Field<int>(texture, 4), vk);
            if (vk) {
                std::fprintf(stderr,
                    "SHENG_TEXTURE_V2 image=%llx memory=%llx offset=%llu bytes=%llu allocflags=%x tiling=%u layout=%u format=%u usage=%x samples=%u levels=%u queue=%x protected=%u sharing=%u\n",
                    (unsigned long long)Field<uint64_t>(vk, 0),
                    (unsigned long long)Field<uint64_t>(vk, 8),
                    (unsigned long long)Field<uint64_t>(vk, 16),
                    (unsigned long long)Field<uint64_t>(vk, 24),
                    Field<uint32_t>(vk, 32), Field<uint32_t>(vk, 64),
                    Field<uint32_t>(vk, 68), Field<uint32_t>(vk, 72),
                    Field<uint32_t>(vk, 76), Field<uint32_t>(vk, 80),
                    Field<uint32_t>(vk, 84), Field<uint32_t>(vk, 88),
                    Field<uint8_t>(vk, 92), Field<uint32_t>(vk, 144));
            }
        }
        // A small real render target distinguishes an invalid context from a
        // rejected external texture. Bounded diagnostics; never a substitute image.
        if (!result && gpu) {
            auto target = reinterpret_cast<Surface (*)(void*, bool, const ImageInfo&)>(dlsym(RTLD_NEXT,
                "_ZN4OHOS5Rosen7Drawing7Surface16MakeRenderTargetEPNS1_10GPUContextEbRKNS1_9ImageInfoE"));
            if (target) {
                ImageInfo info{8, 8, 4, 2, {}};
                auto test = target(gpu, false, info);
                std::fprintf(stderr, "SHENG_SURFACE_CONTEXT_TEST tid=%ld target=%p\n", syscall(SYS_gettid), test.get());
            }
        }
    }
    return result;
}
