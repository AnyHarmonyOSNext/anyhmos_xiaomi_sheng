// Keep cleanup on its owning GPU thread. The gate permits same-thread release
// inline, while all cross-thread tasks retain the donor's original scheduler.
#include "native_surface_lifetime_v1.cpp"
#include <functional>
using TaskV2 = std::function<void()>;
using PostV2 = std::function<void(const TaskV2&)>;

extern "C" void ShengRegisterPostV2(void*, const PostV2&)
    asm("_ZN4OHOS5Rosen7Drawing10GPUContext16RegisterPostFuncERKNSt3__h8functionIFvRKNS4_IFvvEEEEEE");
extern "C" void ShengRegisterPostV2(void* gpu, const PostV2& post)
{
    static auto original = reinterpret_cast<void (*)(void*, const PostV2&)>(dlsym(RTLD_NEXT,
        "_ZN4OHOS5Rosen7Drawing10GPUContext16RegisterPostFuncERKNSt3__h8functionIFvRKNS4_IFvvEEEEEE"));
    if (!original) std::abort();
    const long owner = syscall(SYS_gettid);
    std::fprintf(stderr, "SHENG_POST_V2_REGISTER gpu=%p owner=%ld enabled=%d\n", gpu, owner, bool(post));
    if (!post) { original(gpu, post); return; }
    original(gpu, [post, owner](const TaskV2& task) {
        static unsigned queued = 0, inlineCalls = 0;
        const auto n = __atomic_add_fetch(&queued, 1, __ATOMIC_RELAXED);
        const long caller = syscall(SYS_gettid);
        if (caller == owner && access("/data/local/tmp/sheng-gpu-owner-cleanup", F_OK) == 0) {
            const auto done = __atomic_add_fetch(&inlineCalls, 1, __ATOMIC_RELAXED);
            if (done <= 12 || done % 64 == 0)
                std::fprintf(stderr, "SHENG_POST_V2_INLINE done=%u owner=%ld caller=%ld\n", done, owner, caller);
            task();
            return;
        }
        if (n <= 12 || n % 64 == 0)
            std::fprintf(stderr, "SHENG_POST_V2_QUEUE n=%u owner=%ld caller=%ld\n", n, owner, caller);
        post([task, owner, n]() {
            static unsigned executed = 0;
            const auto done = __atomic_add_fetch(&executed, 1, __ATOMIC_RELAXED);
            if (done <= 12 || done % 64 == 0)
                std::fprintf(stderr, "SHENG_POST_V2_RUN done=%u queued_id=%u owner=%ld actual=%ld\n", done, n, owner, syscall(SYS_gettid));
            task();
        });
    });
}
