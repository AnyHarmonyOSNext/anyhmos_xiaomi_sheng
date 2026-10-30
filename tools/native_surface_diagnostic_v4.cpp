// Additional read-only handle validation at the original donor import boundary.
#include "native_surface_diagnostic_v2.cpp"
#include <cstdlib>
#include <fcntl.h>
#include <sys/stat.h>
#include <cerrno>

extern "C" void* ShengResolveBufferImport()
{
    static void* original = dlsym(RTLD_NEXT,
        "_ZN4OHOS5Rosen17NativeBufferUtils34MakeBackendTextureFromNativeBufferEP18NativeWindowBufferiib");
    if (!original) std::abort();
    return original;
}

extern "C" void ShengObserveBufferImport(const void* backend, void* window,
                                         int width, int height, bool protectedBuffer)
{
    static auto valid = reinterpret_cast<bool (*)(const void*)>(dlsym(RTLD_NEXT,
        "_ZNK4OHOS5Rosen7Drawing14BackendTexture7IsValidEv"));
    static auto texture = reinterpret_cast<const void* (*)(const void*)>(dlsym(RTLD_NEXT,
        "_ZNK4OHOS5Rosen7Drawing14BackendTexture14GetTextureInfoEv"));
    static auto handle = reinterpret_cast<const void* (*)(void*)>(dlsym(RTLD_NEXT,
        "OH_NativeWindow_GetBufferHandleFromNative"));
    static auto native = reinterpret_cast<void* (*)(void*)>(dlsym(RTLD_NEXT,
        "OH_NativeBufferFromNativeWindowBuffer"));
    const bool good = valid && valid(backend);
    static unsigned calls = 0, failures = 0;
    const auto call = __atomic_add_fetch(&calls, 1, __ATOMIC_RELAXED);
    if (call > 24 && (good || __atomic_add_fetch(&failures, 1, __ATOMIC_RELAXED) > 32)) return;
    const void* info = texture ? texture(backend) : nullptr;
    const void* vk = info ? Field<const void*>(info, 24) : nullptr;
    const void* h = handle ? handle(window) : nullptr;
    void* n = native ? native(window) : nullptr;
    std::fprintf(stderr,
        "SHENG_IMPORT_V4 tid=%ld call=%u window=%p native=%p size=%dx%d protected=%d valid=%d vk=%p handle=%p\n",
        syscall(SYS_gettid), call, window, n, width, height, protectedBuffer, good, vk, h);
    if (h) {
        // Donor's 56-byte HDF BufferHandle, not the SDK's 64-byte variant
        // containing key. Read no bytes beyond the fixed header.
        const int fd = Field<int>(h, 0);
        struct stat st{};
        const int statResult = fstat(fd, &st);
        const int statError = errno;
        std::fprintf(stderr,
            "SHENG_HANDLE_V4 fd=%d flags=%d fstat=%d errno=%d fdsize=%llu width=%d height=%d stride=%d size=%d format=%d usage=%llx reserveFds=%u reserveInts=%u\n",
            fd, fcntl(fd, F_GETFD), statResult, statError,
            static_cast<unsigned long long>(st.st_size), Field<int>(h, 4),
            Field<int>(h, 12), Field<int>(h, 8), Field<int>(h, 16), Field<int>(h, 20),
            (unsigned long long)Field<uint64_t>(h, 24), Field<uint32_t>(h, 48), Field<uint32_t>(h, 52));
    }
}
