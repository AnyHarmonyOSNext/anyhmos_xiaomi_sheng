// Linear DMA-heap allocator for the Ace5 display bring-up.
// Implements the unmodified OpenHarmony 6.0 IDisplayBufferVdi ABI.
#include "idisplay_buffer_vdi.h"
#include "log.h"
#include <cerrno>
#include <climits>
#include <cstdlib>
#include <fcntl.h>
#include <linux/dma-buf.h>
#include <linux/dma-heap.h>
#include <sys/ioctl.h>
#include <sys/mman.h>
#include <sys/stat.h>
#include <sys/xattr.h>
#include <unistd.h>

namespace OHOS::HDI::Display::Buffer::V1_0 {
namespace {
constexpr int32_t OK = 0, FAIL = -1, INVALID = -3, UNSUPPORTED = -5;
constexpr uint64_t SUPPORTED_USAGE = 3 | (1ULL << 3) | (1ULL << 4) |
    (1ULL << 6) | (1ULL << 7) | (1ULL << 8) | (1ULL << 9) |
    (1ULL << 10) | (1ULL << 16) | (1ULL << 26) | (1ULL << 27);
#ifndef ACE5_LINEAR_STRIDE_ALIGNMENT
#define ACE5_LINEAR_STRIDE_ALIGNMENT 256
#endif
constexpr uint32_t STRIDE_ALIGNMENT = ACE5_LINEAR_STRIDE_ALIGNMENT;
static_assert(STRIDE_ALIGNMENT && !(STRIDE_ALIGNMENT & (STRIDE_ALIGNMENT-1)));
constexpr uint64_t MAX_SIZE = 256ULL * 1024 * 1024;
constexpr uint64_t CACHED_MEDIA = 1ULL << 5;
constexpr uint64_t PREFER_NO_PADDING = 1ULL << 26;
bool IsSemiPlanar420(uint32_t format) { return format == 24 || format == 25; }
unsigned BytesPerPixel(uint32_t format)
{
    switch (format) {
        case 3: return 2; // PIXEL_FMT_RGB_565
        case 11: case 12: case 19: case 20: return 4;
        default: return 0;
    }
}
bool Layout(uint32_t width, uint32_t height, uint64_t usage, uint32_t format,
    uint32_t &stride, uint64_t &size)
{
    const bool yuv = IsSemiPlanar420(format);
    unsigned bpp = yuv ? 1 : BytesPerPixel(format);
    // The native software video decoder requests DMA | MMZ_CACHE. The system
    // DMA heap is cached and synchronized through DMA_BUF_IOCTL_SYNC. This does
    // not provide MMZ/physical-contiguous memory or protected allocations.
    uint64_t allowed = SUPPORTED_USAGE;
    if (usage & (1ULL << 3)) allowed |= CACHED_MEDIA;
    // BLOB width is a byte count (ASTC backing storage), not image pixels.
    // It must remain a one-dimensional, non-renderable byte allocation.
    if (format == 38) {
        if (!width || height != 1 || width > MAX_SIZE ||
            (usage & ~allowed) || (usage & (7ULL << 8))) return false;
        stride = width; size = width;
        return true;
    }
    if (!width || !height || width > 16384 || height > 16384 || !bpp ||
        (usage & ~allowed) || (yuv && ((width | height) & 1))) return false;
    // Image decoding requests PREFER_NO_PADDING and ALLOC_NO_IPC. The latter
    // is a caller-side allocation-routing hint, with no extra memory layout.
    // Honor the former even in builds whose default RGB stride is aligned.
    // CPU-decoded images can later become GPU textures. PREFER_NO_PADDING
    // is a preference; preserve the linear GPU pitch requirement in all RGB/YUV buffers.
    stride = (width * bpp + STRIDE_ALIGNMENT - 1) & ~(STRIDE_ALIGNMENT - 1);
    size = uint64_t(stride) * height;
    if (yuv) size += uint64_t(stride) * (height / 2);
    return size <= MAX_SIZE;
}
bool Valid(const BufferHandle &h)
{
    uint32_t stride; uint64_t size;
    return h.fd >= 0 && h.reserveFds == 0 && h.reserveInts == 0 &&
        Layout(h.width, h.height, h.usage, h.format, stride, size) &&
        h.stride == int32_t(stride) && h.size >= int64_t(size) &&
        uint64_t(h.size) <= MAX_SIZE;
}
int32_t Sync(const BufferHandle &h, uint64_t flags)
{
    if (!Valid(h)) return INVALID;
    dma_buf_sync sync{flags};
    int rc;
    do { rc = ioctl(h.fd, DMA_BUF_IOCTL_SYNC, &sync); } while (rc < 0 && errno == EINTR);
    return rc == 0 ? OK : FAIL;
}
class LinearBuffer final : public IDisplayBufferVdi {
public:
    int32_t AllocMem(const AllocInfo &info, BufferHandle *&handle) const override
    {
        handle = nullptr;
        Ace5Log("AllocMem width=%u height=%u format=%u usage=0x%llx expected=%u",
            info.width, info.height, info.format, (unsigned long long)info.usage, info.expectedSize);
        uint32_t stride; uint64_t size;
        if (!Layout(info.width, info.height, info.usage, info.format, stride, size)) {
            Ace5Log("AllocMem unsupported layout/usage");
            return UNSUPPORTED;
        }
        if (info.usage & (1ULL << 7)) {
            if (info.expectedSize < size || info.expectedSize > MAX_SIZE) return INVALID;
            size = info.expectedSize;
        }
        size = (size + 4095) & ~4095ULL;
        int heap = open("/dev/dma_heap/system", O_RDONLY | O_CLOEXEC);
        if (heap < 0) {
            const int openError = errno;
            struct stat st{};
            const int statResult = stat("/dev/dma_heap/system", &st);
            const int statError = statResult ? errno : 0;
            char context[160]{};
            const ssize_t contextLength = getxattr("/dev/dma_heap/system", "security.selinux", context, sizeof(context)-1);
            const int contextError = contextLength < 0 ? errno : 0;
            Ace5Log("AllocMem heap open errno=%d stat=%d stat_errno=%d uid=%u gid=%u mode=%o context=%s context_errno=%d",
                openError, statResult, statError, st.st_uid, st.st_gid, st.st_mode & 07777, context, contextError);
            return FAIL;
        }
        dma_heap_allocation_data request{};
        request.len = size; request.fd_flags = O_RDWR | O_CLOEXEC;
        int rc = ioctl(heap, DMA_HEAP_IOCTL_ALLOC, &request);
        int allocError = errno;
        close(heap);
        if (rc) { Ace5Log("AllocMem heap ioctl errno=%d size=%llu", allocError,
            (unsigned long long)size); return FAIL; }
        auto *h = static_cast<BufferHandle *>(calloc(1, sizeof(BufferHandle)));
        if (!h) { close(request.fd); return FAIL; }
        h->fd = request.fd; h->width = info.width; h->height = info.height;
        h->stride = stride; h->size = size; h->format = info.format; h->usage = info.usage;
        handle = h;
        Ace5Log("AllocMem success fd=%d stride=%u size=%llu", h->fd, stride,
            (unsigned long long)size);
        return OK;
    }
    void FreeMem(const BufferHandle &handle) const override
    {
        // The VDI owns both the FD and malloc-allocated handle, as in GbmFreeMem.
        auto &h = const_cast<BufferHandle &>(handle);
        if (h.virAddr && h.virAddr != MAP_FAILED && h.size > 0) munmap(h.virAddr, h.size);
        if (h.fd >= 0) close(h.fd);
        for (uint32_t i = 0; i < h.reserveFds; ++i)
            if (h.reserve[i] >= 0) close(h.reserve[i]);
        free(&h);
    }
    void *Mmap(const BufferHandle &handle) const override
    {
        if (!Valid(handle)) return nullptr;
        auto &h = const_cast<BufferHandle &>(handle);
        if (h.virAddr && h.virAddr != MAP_FAILED) return h.virAddr;
        void *p = mmap(nullptr, h.size, PROT_READ | PROT_WRITE, MAP_SHARED, h.fd, 0);
        if (p == MAP_FAILED) return nullptr;
        h.virAddr = p;
        return p;
    }
    int32_t Unmap(const BufferHandle &handle) const override
    {
        if (!Valid(handle) || !handle.virAddr || handle.virAddr == MAP_FAILED) return INVALID;
        auto &h = const_cast<BufferHandle &>(handle);
        if (munmap(h.virAddr, h.size)) return FAIL;
        h.virAddr = nullptr;
        return OK;
    }
    int32_t FlushCache(const BufferHandle &h) const override
    { return Sync(h, DMA_BUF_SYNC_END | DMA_BUF_SYNC_RW); }
    int32_t InvalidateCache(const BufferHandle &h) const override
    { return Sync(h, DMA_BUF_SYNC_START | DMA_BUF_SYNC_RW); }
    int32_t IsSupportedAlloc(const std::vector<VerifyAllocInfo> &infos,
        std::vector<bool> &supported) const override
    {
        supported.clear();
        for (const auto &i : infos) {
            uint32_t stride; uint64_t size;
            supported.push_back(Layout(i.width, i.height, i.usage, i.format, stride, size));
        }
        return OK;
    }
    int32_t RegisterBuffer(const BufferHandle &h) override
    { return Valid(h) && fcntl(h.fd, F_GETFD) >= 0 ? OK : INVALID; }
    int32_t SetMetadata(const BufferHandle &, uint32_t, const std::vector<uint8_t> &) override
    { return UNSUPPORTED; }
    int32_t GetMetadata(const BufferHandle &, uint32_t, std::vector<uint8_t> &) override
    { return UNSUPPORTED; }
    int32_t ListMetadataKeys(const BufferHandle &, std::vector<uint32_t> &) override
    { return UNSUPPORTED; }
    int32_t EraseMetadataKey(const BufferHandle &, uint32_t) override
    { return UNSUPPORTED; }
    int32_t GetImageLayout(const BufferHandle &h, V1_2::ImageLayout &layout) const override
    {
        if (!Valid(h)) return INVALID;
        layout.pixelFormat = h.format;
        layout.planes = {{0, uint32_t(h.stride), uint32_t(h.height)}};
        if (IsSemiPlanar420(h.format)) {
            layout.planes.push_back({uint32_t(h.stride) * uint32_t(h.height),
                uint32_t(h.stride), uint32_t(h.height / 2)});
        }
        return OK;
    }
};
static_assert(sizeof(BufferHandle) == 56);
static_assert(sizeof(AllocInfo) == 24);
static_assert(sizeof(V1_2::ImagePlane) == 16);
}
extern "C" IDisplayBufferVdi *CreateDisplayBufferVdi() { return new LinearBuffer; }
extern "C" void DestroyDisplayBufferVdi(IDisplayBufferVdi *vdi) { delete vdi; }
}
