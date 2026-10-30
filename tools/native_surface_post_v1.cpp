// Preserve the registered queue and task while observing actual execution.
#include "native_surface_lifetime_v1.cpp"
#include <functional>
using TaskV1 = std::function<void()>;
using PostV1 = std::function<void(const TaskV1&)>;

extern "C" void ShengRegisterPost(void*, const PostV1&)
    asm("_ZN4OHOS5Rosen7Drawing10GPUContext16RegisterPostFuncERKNSt3__h8functionIFvRKNS4_IFvvEEEEEE");
extern "C" void ShengRegisterPost(void* gpu, const PostV1& post)
{
    static auto original = reinterpret_cast<void (*)(void*, const PostV1&)>(dlsym(RTLD_NEXT,
        "_ZN4OHOS5Rosen7Drawing10GPUContext16RegisterPostFuncERKNSt3__h8functionIFvRKNS4_IFvvEEEEEE"));
    if (!original) std::abort();
    const long owner = syscall(SYS_gettid);
    std::fprintf(stderr, "SHENG_POST_REGISTER gpu=%p owner=%ld enabled=%d\n", gpu, owner, bool(post));
    if (!post) { original(gpu, post); return; }
    original(gpu, [post, owner](const TaskV1& task) {
        static unsigned queued = 0;
        const auto n = __atomic_add_fetch(&queued, 1, __ATOMIC_RELAXED);
        if (n <= 12 || n % 64 == 0)
            std::fprintf(stderr, "SHENG_POST_QUEUE n=%u owner=%ld caller=%ld\n", n, owner, syscall(SYS_gettid));
        post([task, owner, n]() {
            static unsigned executed = 0;
            const auto done = __atomic_add_fetch(&executed, 1, __ATOMIC_RELAXED);
            if (done <= 12 || done % 64 == 0)
                std::fprintf(stderr, "SHENG_POST_RUN done=%u queued_id=%u owner=%ld actual=%ld\n", done, n, owner, syscall(SYS_gettid));
            task();
        });
    });
}
