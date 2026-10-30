// Observe wrapper destruction without changing the donor's destructors.
#include "native_surface_diagnostic_v6.cpp"

extern "C" void ShengImageD0(void*)
    asm("_ZN4OHOS5Rosen7Drawing5ImageD0Ev");
extern "C" void ShengImageD0(void* self)
{
    static auto fn = reinterpret_cast<void (*)(void*)>(dlsym(RTLD_NEXT,
        "_ZN4OHOS5Rosen7Drawing5ImageD0Ev"));
    if (!fn) std::abort();
    static unsigned calls = 0;
    const auto n = __atomic_add_fetch(&calls, 1, __ATOMIC_RELAXED);
    if (n <= 12 || n % 64 == 0)
        std::fprintf(stderr, "SHENG_IMAGE_D0 n=%u self=%p tid=%ld\n", n, self, syscall(SYS_gettid));
    fn(self);
}

extern "C" void ShengImageD1(void*)
    asm("_ZN4OHOS5Rosen7Drawing5ImageD1Ev");
extern "C" void ShengImageD1(void* self)
{
    static auto fn = reinterpret_cast<void (*)(void*)>(dlsym(RTLD_NEXT,
        "_ZN4OHOS5Rosen7Drawing5ImageD1Ev"));
    if (!fn) std::abort();
    static unsigned calls = 0;
    const auto n = __atomic_add_fetch(&calls, 1, __ATOMIC_RELAXED);
    if (n <= 12 || n % 64 == 0)
        std::fprintf(stderr, "SHENG_IMAGE_D1 n=%u self=%p tid=%ld\n", n, self, syscall(SYS_gettid));
    fn(self);
}
