// Preserve the v2 Surface observations, adding read-only native imports.
#include "native_surface_diagnostic_v2.cpp"
#include <cstdlib>

extern "C" void* ShengResolveBufferImport()
{
    static void* original = dlsym(RTLD_NEXT,
        "_ZN4OHOS5Rosen17NativeBufferUtils34MakeBackendTextureFromNativeBufferEP18NativeWindowBufferiib");
    if (!original) {
        std::fprintf(stderr, "SHENG_IMPORT_ORIGINAL_MISSING %s\n", dlerror());
        std::abort();
    }
    return original;
}

extern "C" void ShengObserveBufferImport(const void* backend, void* window,
                                         int width, int height, bool protectedBuffer)
{
    static auto valid = reinterpret_cast<bool (*)(const void*)>(dlsym(RTLD_NEXT,
        "_ZNK4OHOS5Rosen7Drawing14BackendTexture7IsValidEv"));
    static auto texture = reinterpret_cast<const void* (*)(const void*)>(dlsym(RTLD_NEXT,
        "_ZNK4OHOS5Rosen7Drawing14BackendTexture14GetTextureInfoEv"));
    const bool good = valid && valid(backend);
    static unsigned calls = 0, failures = 0;
    const auto call = __atomic_add_fetch(&calls, 1, __ATOMIC_RELAXED);
    if (call > 60 && (good || __atomic_add_fetch(&failures, 1, __ATOMIC_RELAXED) > 40)) return;
    const void* info = texture ? texture(backend) : nullptr;
    const void* vk = info ? Field<const void*>(info, 24) : nullptr;
    std::fprintf(stderr,
        "SHENG_IMPORT_V3 tid=%ld call=%u window=%p size=%dx%d protected=%d backend=%p valid=%d info=%p vk=%p\n",
        syscall(SYS_gettid), call, window, width, height, protectedBuffer, backend, good, info, vk);
    if (vk) std::fprintf(stderr,
        "SHENG_IMPORT_V3 image=%llx memory=%llx format=%u usage=%x layout=%u queue=%x\n",
        (unsigned long long)Field<uint64_t>(vk, 0),
        (unsigned long long)Field<uint64_t>(vk, 8), Field<uint32_t>(vk, 72),
        Field<uint32_t>(vk, 76), Field<uint32_t>(vk, 68), Field<uint32_t>(vk, 88));
}
