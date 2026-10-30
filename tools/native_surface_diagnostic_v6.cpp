// Read-only observation of image creation and cache format comparisons.
#include "native_surface_diagnostic_v5.cpp"
struct BitmapFormatV6 { uint32_t color, alpha; };

extern "C" bool ShengObserveImage(void*, void*, const void*, uint32_t,
    BitmapFormatV6, const Surface&, void (*)(void*), void*, bool)
    asm("_ZN4OHOS5Rosen7Drawing5Image16BuildFromTextureERNS1_10GPUContextERKNS1_11TextureInfoENS1_13TextureOriginENS1_12BitmapFormatERKNSt3__h10shared_ptrINS1_10ColorSpaceEEEPFvPvESG_b");
extern "C" bool ShengObserveImage(void* self, void* gpu, const void* texture,
    uint32_t origin, BitmapFormatV6 format, const Surface& color,
    void (*cleanup)(void*), void* helper, bool ignoreAlpha)
{
    using Fn = bool (*)(void*, void*, const void*, uint32_t, BitmapFormatV6,
        const Surface&, void (*)(void*), void*, bool);
    static auto original = reinterpret_cast<Fn>(dlsym(RTLD_NEXT,
        "_ZN4OHOS5Rosen7Drawing5Image16BuildFromTextureERNS1_10GPUContextERKNS1_11TextureInfoENS1_13TextureOriginENS1_12BitmapFormatERKNSt3__h10shared_ptrINS1_10ColorSpaceEEEPFvPvESG_b"));
    if (!original) std::abort();
#ifdef SHENG_BEFORE_IMAGE
    SHENG_BEFORE_IMAGE(gpu);
#endif
    const bool result = original(self, gpu, texture, origin, format, color,
        cleanup, helper, ignoreAlpha);
    static unsigned calls = 0, failed = 0;
    const auto n = __atomic_add_fetch(&calls, 1, __ATOMIC_RELAXED);
    if (n <= 12 || n % 64 == 0 || (!result && __atomic_add_fetch(&failed, 1, __ATOMIC_RELAXED) <= 16))
        std::fprintf(stderr, "SHENG_IMAGE_V6 n=%u result=%d self=%p gpu=%p texture=%p color=%u alpha=%u cleanup=%p helper=%p\n",
            n, result, self, gpu, texture, format.color, format.alpha,
            reinterpret_cast<void*>(cleanup), helper);
    return result;
}

extern "C" bool ShengObserveCompare(void*, uint32_t, uint32_t)
    asm("_ZN4OHOS5Rosen17NativeBufferUtils27IsYcbcrModelOrRangeNotEqualEP15OH_NativeBuffer29VkSamplerYcbcrModelConversion19VkSamplerYcbcrRange");
extern "C" bool ShengObserveCompare(void* native, uint32_t model, uint32_t range)
{
    using Fn = bool (*)(void*, uint32_t, uint32_t);
    static auto original = reinterpret_cast<Fn>(dlsym(RTLD_NEXT,
        "_ZN4OHOS5Rosen17NativeBufferUtils27IsYcbcrModelOrRangeNotEqualEP15OH_NativeBuffer29VkSamplerYcbcrModelConversion19VkSamplerYcbcrRange"));
    if (!original) std::abort();
    const bool result = original(native, model, range);
    static unsigned calls = 0, different = 0;
    const auto n = __atomic_add_fetch(&calls, 1, __ATOMIC_RELAXED);
    if (n <= 12 || (result && __atomic_add_fetch(&different, 1, __ATOMIC_RELAXED) <= 16))
        std::fprintf(stderr, "SHENG_COMPARE_V6 n=%u different=%d native=%p cached_model=%u cached_range=%u\n",
            n, result, native, model, range);
    return result;
}
