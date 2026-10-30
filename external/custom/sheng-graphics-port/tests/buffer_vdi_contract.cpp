#include "idisplay_buffer_vdi.h"
#include <cstdio>
#include <cstring>
#include <dlfcn.h>
#include <fcntl.h>
#include <unistd.h>
using namespace OHOS::HDI::Display::Buffer::V1_0;
#define CHECK(x) do { if (!(x)) { printf("FAIL line=%d: %s\n", __LINE__, #x); return 1; } } while (0)
int main(int argc, char **argv)
{
    setbuf(stdout, nullptr); alarm(15);
    CHECK(argc == 2);
    void *so = dlopen(argv[1], RTLD_NOW | RTLD_LOCAL);
    if (!so) { puts(dlerror()); return 1; }
    auto create = reinterpret_cast<CreateDisplayBufferVdiFunc>(dlsym(so, "CreateDisplayBufferVdi"));
    auto destroy = reinterpret_cast<DestroyDisplayBufferVdiFunc>(dlsym(so, "DestroyDisplayBufferVdi"));
    CHECK(create && destroy);
    auto *vdi = create(); CHECK(vdi);
    for (int i = 0; i < 64; ++i) {
        BufferHandle *h = nullptr;
        AllocInfo info{257, 129, 3 | (1ULL << 3), 12, 0};
        CHECK(vdi->AllocMem(info, h) == 0 && h);
        CHECK(h->stride >= 257 * 4 && h->size >= h->stride * 129);
        CHECK(vdi->RegisterBuffer(*h) == 0);
        auto *p = static_cast<unsigned char *>(vdi->Mmap(*h)); CHECK(p);
        CHECK(vdi->InvalidateCache(*h) == 0);
        memset(p, 0xa5, h->size);
        CHECK(vdi->FlushCache(*h) == 0);
        CHECK(vdi->Unmap(*h) == 0);
        p = static_cast<unsigned char *>(vdi->Mmap(*h)); CHECK(p);
        CHECK(vdi->InvalidateCache(*h) == 0);
        CHECK(p[0] == 0xa5 && p[h->size - 1] == 0xa5);
        CHECK(vdi->FlushCache(*h) == 0);
        OHOS::HDI::Display::Buffer::V1_2::ImageLayout layout{};
        CHECK(vdi->GetImageLayout(*h, layout) == 0);
        CHECK(layout.planes.size() == 1 && layout.planes[0].hStride == unsigned(h->stride));
        int fd = h->fd;
        vdi->FreeMem(*h);
        CHECK(fcntl(fd, F_GETFD) == -1);
    }
    BufferHandle *h = nullptr;
    for (uint32_t format : {3U, 12U, 20U}) {
        CHECK(vdi->AllocMem({325, 323, 0xc00002b, format, 0}, h) == 0 && h);
        CHECK(h->stride == 325 * (format == 3 ? 2 : 4));
        CHECK(h->usage == 0xc00002b && vdi->RegisterBuffer(*h) == 0);
        auto *p = static_cast<unsigned char *>(vdi->Mmap(*h)); CHECK(p);
        CHECK(vdi->InvalidateCache(*h) == 0);
        for (int i = 0; i < h->size; ++i) p[i] = (i * 31 + 7) & 255;
        CHECK(vdi->FlushCache(*h) == 0 && vdi->Unmap(*h) == 0);
        p = static_cast<unsigned char *>(vdi->Mmap(*h)); CHECK(p);
        CHECK(vdi->InvalidateCache(*h) == 0);
        for (int i = 0; i < h->size; ++i) CHECK(p[i] == ((i * 31 + 7) & 255));
        CHECK(vdi->FlushCache(*h) == 0);
        vdi->FreeMem(*h); h = nullptr;
    }
    CHECK(vdi->AllocMem({325, 323, 0xc00002b | (1ULL << 11), 20, 0}, h) == -5 && !h);
    CHECK(vdi->AllocMem({325, 323, 0xc00002b | (1ULL << 28), 20, 0}, h) == -5 && !h);
    for (uint32_t format : {24U, 25U}) {
        for (auto dims : {std::pair<uint32_t, uint32_t>{1080, 2340}, {1280, 2832}, {258, 130}}) {
            CHECK(vdi->AllocMem({dims.first, dims.second, 0x42b, format, 0}, h) == 0 && h);
            CHECK(vdi->RegisterBuffer(*h) == 0);
            OHOS::HDI::Display::Buffer::V1_2::ImageLayout layout{};
            CHECK(vdi->GetImageLayout(*h, layout) == 0 && layout.pixelFormat == format);
            CHECK(layout.planes.size() == 2);
            size_t uv = size_t(h->stride) * h->height;
            size_t end = uv + size_t(h->stride) * (h->height / 2);
            CHECK(layout.planes[1].offset == uv && end <= size_t(h->size));
            auto *p = static_cast<unsigned char *>(vdi->Mmap(*h)); CHECK(p);
            CHECK(vdi->InvalidateCache(*h) == 0);
            memset(p, 0x51, uv); memset(p + uv, 0x80, end - uv);
            memset(p + end, 0xcd, h->size - end);
            CHECK(vdi->FlushCache(*h) == 0 && vdi->Unmap(*h) == 0);
            p = static_cast<unsigned char *>(vdi->Mmap(*h)); CHECK(p);
            CHECK(vdi->InvalidateCache(*h) == 0);
            CHECK(p[0] == 0x51 && p[uv - 1] == 0x51 && p[uv] == 0x80 && p[end - 1] == 0x80);
            for (size_t i = end; i < size_t(h->size); ++i) CHECK(p[i] == 0xcd);
            CHECK(vdi->FlushCache(*h) == 0);
            vdi->FreeMem(*h); h = nullptr;
        }
    }
    CHECK(vdi->AllocMem({257, 128, 0x42b, 24, 0}, h) == -5 && !h);
    CHECK(vdi->AllocMem({256, 129, 0x42b, 24, 0}, h) == -5 && !h);
    CHECK(vdi->AllocMem({256, 128, 0x42b | (1ULL << 11), 24, 0}, h) == -5 && !h);
    CHECK(vdi->AllocMem({256, 128, 1ULL << 5, 24, 0}, h) == -5 && !h);
    CHECK(vdi->AllocMem({64, 64, 1ULL << 11, 12, 0}, h) == -5 && !h);
    CHECK(vdi->AllocMem({0xffffffff, 64, 3, 12, 0}, h) == -5 && !h);
    CHECK(vdi->AllocMem({64, 64, 3, 0x7fff0001, 0}, h) == -5 && !h);
    std::vector<VerifyAllocInfo> infos{{64,64,3,12},{64,64,1ULL << 11,12}};
    std::vector<bool> supported;
    CHECK(vdi->IsSupportedAlloc(infos, supported) == 0);
    CHECK(supported.size() == 2 && supported[0] && !supported[1]);
    for (uint32_t bytes : {uint32_t(879760), uint32_t(1301)}) {
        BufferHandle *blob = nullptr;
        CHECK(vdi->AllocMem({bytes,1,0x2b,38,0},blob) == 0);
        CHECK(blob && blob->stride == int(bytes) && blob->size >= int(bytes));
        CHECK(vdi->RegisterBuffer(*blob) == 0);
        auto *data = static_cast<unsigned char *>(vdi->Mmap(*blob)); CHECK(data);
        data[0] = 0x51; data[bytes-1] = 0x93;
        CHECK(vdi->FlushCache(*blob) == 0 && vdi->Unmap(*blob) == 0);
        data = static_cast<unsigned char *>(vdi->Mmap(*blob)); CHECK(data);
        CHECK(vdi->InvalidateCache(*blob) == 0 && data[0] == 0x51 && data[bytes-1] == 0x93);
        vdi->FreeMem(*blob);
    }
    CHECK(vdi->AllocMem({879760,2,0x2b,38,0},h) == -5 && !h);
    CHECK(vdi->AllocMem({879760,1,0x12b,38,0},h) == -5 && !h);
    destroy(vdi); dlclose(so);
    puts("BUFFER_VDI_CONTRACT_RESULT=0 rgb_cycles=64 image_cycles=3 yuv_cycles=6 blob_cycles=2 protected_rejected=1 overflow_rejected=1");
    return 0;
}
