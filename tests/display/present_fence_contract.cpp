#include "composer_exports.h"
#include <cerrno>
#include <cstdio>
#include <cstdlib>
#include <fcntl.h>
#include <unistd.h>
#include <xf86drm.h>
#include <xf86drmMode.h>

using namespace OHOS::HDI::Display::Composer;
extern "C" void Ace5InitializeSubmitForTest();
extern "C" int32_t Ace5SubmitInternalForTest();
extern "C" int32_t Ace5TestClientBuffer(uint32_t);
namespace {
uint64_t *fenceSlot = nullptr;
uint32_t nextFb = 100, removed = 0;
int failure = 0, createdFd = -1;
bool omitFence = false, useZero = false;
void Check(bool passed, const char *message)
{
    if (!passed) { fprintf(stderr, "PRESENT_CONTRACT_FAIL %s\n", message); exit(1); }
}
bool Closed(int fd) { return fcntl(fd, F_GETFD) == -1 && errno == EBADF; }
}
extern "C" drmModeAtomicReq *__real_drmModeAtomicAlloc();
extern "C" int __real_drmModeAtomicAddProperty(drmModeAtomicReq *, uint32_t, uint32_t, uint64_t);
extern "C" drmModeAtomicReq *__wrap_drmModeAtomicAlloc()
{ fenceSlot = nullptr; return __real_drmModeAtomicAlloc(); }
extern "C" int __wrap_drmModeAtomicAddProperty(drmModeAtomicReq *req, uint32_t object,
    uint32_t property, uint64_t value)
{
    if (property == 999) fenceSlot = reinterpret_cast<uint64_t *>(value);
    return __real_drmModeAtomicAddProperty(req, object, property, value);
}
extern "C" int __wrap_drmPrimeFDToHandle(int, int, uint32_t *handle)
{ *handle = 1; return 0; }
extern "C" int __wrap_drmModeAddFB2(int, uint32_t, uint32_t, uint32_t,
    const uint32_t[4], const uint32_t[4], const uint32_t[4], uint32_t *fb, uint32_t)
{ *fb = ++nextFb; return 0; }
extern "C" int __wrap_drmModeRmFB(int, uint32_t fb) { removed = fb; return 0; }
// 模拟驱动在提交失败前已创建 fence 的情况
extern "C" int __wrap_drmModeAtomicCommit(int, drmModeAtomicReq *, uint32_t flags, void *)
{
    if (flags & DRM_MODE_ATOMIC_TEST_ONLY) {
        Check(!fenceSlot, "test-only has no fence side effect"); return 0;
    }
    Check(!(flags & DRM_MODE_ATOMIC_NONBLOCK), "old framebuffer cleanup requires blocking commit");
    Check(fenceSlot && *fenceSlot == UINT64_MAX, "64-bit fence slot initialized");
    if (!omitFence) {
        if (useZero) close(0);
        createdFd = open("/dev/null", O_RDONLY);
        Check(createdFd >= 0, "mock fence opened");
        *fenceSlot = createdFd;
    }
    errno = EINVAL; return failure;
}
int main()
{
    Ace5InitializeSubmitForTest();
    int32_t fence = -1;
    Check(Commit(0, fence) == 0 && fence == createdFd && !Closed(fence), "ownership transferred");
    Check(fcntl(fence, F_GETFD) & FD_CLOEXEC, "fence not inherited across exec");
    close(fence);
    failure = -1;
    Check(Commit(0, fence) != 0 && fence == -1 && Closed(createdFd) && removed == 102,
        "failure closes fence and removes only candidate framebuffer");
    failure = 0;
    Check(Ace5TestClientBuffer(0) == 0 && removed == 103, "test-only releases candidate");
    Check(Ace5SubmitInternalForTest() == 0 && Closed(createdFd) && removed == 101,
        "internal submission closes unused fence");
    omitFence = true;
    Check(Commit(0, fence) == 0 && fence == -1 && removed == 104,
        "missing fence does not undo successful submission");
    omitFence = false; useZero = true;
    Check(Commit(0, fence) == 0 && fence == 0 && !Closed(0), "descriptor zero transferred");
    close(fence); failure = -1;
    Check(Commit(0, fence) != 0 && fence == -1 && Closed(0) && removed == 107,
        "descriptor zero closed on failure");
    puts("PRESENT_CONTRACT_OK ownership failure test_only internal missing_fd descriptor_zero");
    return 0;
}
