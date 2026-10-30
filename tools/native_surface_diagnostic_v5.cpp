// Observe the original native-image release boundary; keep ownership unchanged.
#include "native_surface_diagnostic_v4.cpp"

extern "C" void ShengObserveDelete(void*)
    asm("_ZN4OHOS5Rosen17NativeBufferUtils13DeleteVkImageEPv");
extern "C" void ShengObserveDelete(void* helper)
{
    static auto original = reinterpret_cast<void (*)(void*)>(dlsym(RTLD_NEXT,
        "_ZN4OHOS5Rosen17NativeBufferUtils13DeleteVkImageEPv"));
    if (!original) std::abort();
    static unsigned calls = 0;
    const auto n = __atomic_add_fetch(&calls, 1, __ATOMIC_RELAXED);
    if (n <= 16 || n % 64 == 0) {
        std::fprintf(stderr,
            "SHENG_DELETE_V5 n=%u helper=%p refs=%u device=%p image=%p memory=%p\n",
            n, helper, helper ? Field<uint32_t>(helper, 56) : 0,
            helper ? Field<void*>(helper, 0) : nullptr,
            helper ? Field<void*>(helper, 8) : nullptr,
            helper ? Field<void*>(helper, 16) : nullptr);
    }
    original(helper);
}
