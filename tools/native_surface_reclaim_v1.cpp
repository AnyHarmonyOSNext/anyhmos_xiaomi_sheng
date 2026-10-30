// Gated completion/purge experiment on the caller's own Drawing GPU context.
extern "C" void ShengMaybeReclaim(void*);
#define SHENG_BEFORE_IMAGE(gpu) ShengMaybeReclaim(gpu)
#include "native_surface_diagnostic_v6.cpp"

extern "C" void ShengReclaimContext(void* gpu)
{
    using Usage = void (*)(const void*, int*, size_t*);
    using Flush = void (*)(void*, bool);
    static auto usage = reinterpret_cast<Usage>(dlsym(RTLD_NEXT,
        "_ZNK4OHOS5Rosen7Drawing10GPUContext21GetResourceCacheUsageEPiPm"));
    static auto flush = reinterpret_cast<Flush>(dlsym(RTLD_NEXT,
        "_ZN4OHOS5Rosen7Drawing10GPUContext14FlushAndSubmitEb"));
    static auto purge = reinterpret_cast<Flush>(dlsym(RTLD_NEXT,
        "_ZN4OHOS5Rosen7Drawing10GPUContext22PurgeUnlockedResourcesEb"));
    if (!gpu || !usage || !flush || !purge) {
        std::fprintf(stderr, "SHENG_RECLAIM_MISSING gpu=%p\n", gpu);
        return;
    }
    int beforeCount = 0, afterCount = 0;
    size_t beforeBytes = 0, afterBytes = 0;
    usage(gpu, &beforeCount, &beforeBytes);
    flush(gpu, true);
    purge(gpu, false);
    usage(gpu, &afterCount, &afterBytes);
    std::fprintf(stderr, "SHENG_RECLAIM gpu=%p count=%d->%d bytes=%zu->%zu\n",
        gpu, beforeCount, afterCount, beforeBytes, afterBytes);
}

extern "C" void ShengMaybeReclaim(void* gpu)
{
    static thread_local unsigned calls = 0;
    if (++calls % 32 != 0 || access("/data/local/tmp/sheng-gpu-reclaim-test", F_OK) != 0) return;
    ShengReclaimContext(gpu);
}
