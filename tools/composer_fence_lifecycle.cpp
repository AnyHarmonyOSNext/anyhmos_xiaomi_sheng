// Regression: the original HDI responser transfers incoming acquire FDs.
#include "composer_exports.h"
#include <cassert>
#include <cerrno>
#include <cstdio>
#include <dirent.h>
#include <fcntl.h>
#include <sys/eventfd.h>
#include <unistd.h>
using namespace OHOS::HDI::Display::Composer;
namespace OHOS::HDI::Display::Composer { extern "C" void Ace5InitializeVsyncForTest(); }
static unsigned CountFds()
{
    auto *d = opendir("/proc/self/fd"); assert(d);
    unsigned n = 0; while (readdir(d)) ++n;
    closedir(d); return n;
}
int main()
{
    setbuf(stdout, nullptr);
    const unsigned initial = CountFds();
    Ace5InitializeVsyncForTest();
    BufferHandle buffer{};
    buffer.fd = open("/dev/null", O_RDWR | O_CLOEXEC); assert(buffer.fd >= 0);
    buffer.width = buffer.height = 32; buffer.stride = 128; buffer.size = 4096;
    buffer.format = OHOS::HDI::Display::Composer::V1_0::PIXEL_FMT_RGBA_8888;
    LayerInfo info{}; info.width = info.height = 32;
    uint32_t layer = 0; assert(CreateLayer(0, info, layer) == 0);
    const unsigned before = CountFds();
    for (unsigned i = 0; i < 10000; ++i) {
        int clientFence = eventfd(1, EFD_CLOEXEC); assert(clientFence >= 0);
        assert(SetDisplayClientBuffer(0, buffer, clientFence) == 0);
        int layerFence = eventfd(1, EFD_CLOEXEC); assert(layerFence >= 0);
        assert(SetLayerBuffer(0, layer, buffer, layerFence) == 0);
        if (i == 399 && CountFds() > before + 4) {
            printf("FENCE_LOOP_LEAK frames=400 baseline=%u after=%u\n", before, CountFds());
            return 20;
        }
    }
    const unsigned after = CountFds();
    printf("FENCE_LOOP frames=10000 baseline=%u after=%u\n", before, after);
    assert(after <= before + 4);
    int invalid = eventfd(1, EFD_CLOEXEC);
    assert(SetDisplayClientBuffer(99, buffer, invalid) != 0);
    assert(fcntl(invalid, F_GETFD) == -1 && errno == EBADF);
    invalid = eventfd(1, EFD_CLOEXEC);
    assert(SetLayerBuffer(0, layer + 1, buffer, invalid) != 0);
    assert(fcntl(invalid, F_GETFD) == -1 && errno == EBADF);
    int fd = buffer.fd; buffer.fd = -1;
    invalid = eventfd(1, EFD_CLOEXEC);
    assert(SetDisplayClientBuffer(0, buffer, invalid) != 0);
    assert(fcntl(invalid, F_GETFD) == -1 && errno == EBADF);
    assert(fcntl(fd, F_GETFD) >= 0);
    close(fd);
    assert(DestroyVdiImpl() == 0);
    assert(CountFds() == initial);
    puts("COMPOSER_FENCE_LIFECYCLE_OK no_leak=1 failures_close_incoming=1 buffer_fd_borrowed=1");
}
