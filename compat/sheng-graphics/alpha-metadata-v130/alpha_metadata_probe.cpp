// Real DMA buffers, original VDI ABI, cross-process metadata and pixel guards.
#include "idisplay_buffer_vdi.h"
#include <cstdio>
#include <cstring>
#include <dlfcn.h>
#include <sys/wait.h>
#include <unistd.h>
using namespace OHOS::HDI::Display::Buffer::V1_0;
#define CHECK(x) do { if (!(x)) { printf("FAIL line=%d %s\n", __LINE__, #x); return 1; } } while (0)
int main(int argc, char **argv) {
    setbuf(stdout, nullptr); alarm(20); CHECK(argc == 2);
    void *so = dlopen(argv[1], RTLD_NOW | RTLD_LOCAL); CHECK(so);
    auto create = (CreateDisplayBufferVdiFunc)dlsym(so, "CreateDisplayBufferVdi");
    auto destroy = (DestroyDisplayBufferVdiFunc)dlsym(so, "DestroyDisplayBufferVdi");
    CHECK(create && destroy); auto *v = create(); CHECK(v);
    for (uint32_t format : {3u, 11u, 12u, 19u, 20u, 24u, 25u, 28u, 29u}) {
        BufferHandle *h = nullptr;
        CHECK(!v->AllocMem({64, 64, 0x409, format, 0}, h) && h);
        const bool yuv = format >= 24;
        const size_t pixelBytes = size_t(h->stride) * 64 * (yuv ? 3 : 2) / 2;
        CHECK(h->size >= int(pixelBytes + 4096));
        auto *pixels = static_cast<unsigned char *>(v->Mmap(*h)); CHECK(pixels);
        CHECK(!v->InvalidateCache(*h)); memset(pixels, 0xa7, pixelBytes);
        CHECK(!v->FlushCache(*h)); CHECK(!v->Unmap(*h));
        std::vector<uint8_t> color(16, 0); color[0] = 1; color[4] = 1; color[8] = 1;
        uint32_t crop[4] = {0, 0, 64, 64}; std::vector<uint8_t> rect(16);
        memcpy(rect.data(), crop, 16);
        CHECK(!v->SetMetadata(*h, 1, color)); CHECK(!v->SetMetadata(*h, 7, rect));
        int32_t alpha = -1; std::vector<uint8_t> alphaBytes(4);
        memcpy(alphaBytes.data(), &alpha, 4); CHECK(!v->SetMetadata(*h, 12, alphaBytes));
        pid_t child = fork(); CHECK(child >= 0);
        if (!child) {
            BufferHandle imported = *h; imported.fd = dup(h->fd); imported.virAddr = nullptr;
            std::vector<uint8_t> got;
            if (imported.fd < 0 || v->RegisterBuffer(imported) ||
                v->GetMetadata(imported, 1, got) || got != color ||
                v->GetMetadata(imported, 7, got) || got != rect) _exit(2);
            if (v->GetMetadata(imported, 12, got) || got != alphaBytes) _exit(4);
            alpha = 127; memcpy(alphaBytes.data(), &alpha, 4);
            if (v->SetMetadata(imported, 12, alphaBytes)) _exit(5);
            uint32_t update[4] = {2, 4, 32, 24}; memcpy(rect.data(), update, 16);
            int rc = v->SetMetadata(imported, 7, rect); close(imported.fd); _exit(rc ? 3 : 0);
        }
        int status; CHECK(waitpid(child, &status, 0) == child);
        CHECK(WIFEXITED(status) && WEXITSTATUS(status) == 0);
        uint32_t updated[4] = {2, 4, 32, 24}; std::vector<uint8_t> got;
        CHECK(!v->GetMetadata(*h, 7, got) && got.size() == 16 && !memcmp(got.data(), updated, 16));
        CHECK(!v->GetMetadata(*h, 12, got) && got.size() == 4);
        memcpy(&alpha, got.data(), 4); CHECK(alpha == 127);
        for (int32_t invalid : {-2, 256}) {
            memcpy(alphaBytes.data(), &invalid, 4); CHECK(v->SetMetadata(*h, 12, alphaBytes) != 0);
        }
        CHECK(v->SetMetadata(*h, 12, std::vector<uint8_t>(8)) != 0);
        CHECK(v->SetMetadata(*h, 10, alphaBytes) != 0);
        CHECK(v->SetMetadata(*h, 11, alphaBytes) != 0);
        CHECK(v->SetMetadata(*h, 1, std::vector<uint8_t>(4)) != 0);
        CHECK(v->SetMetadata(*h, 31, color) != 0);
        crop[2] = 65; memcpy(rect.data(), crop, 16); CHECK(v->SetMetadata(*h, 7, rect) != 0);
        BufferHandle truncated = *h; truncated.size -= 4096;
        CHECK(v->GetMetadata(truncated, 1, got) != 0);
        std::vector<uint32_t> keys; CHECK(!v->ListMetadataKeys(*h, keys));
        CHECK(keys == (std::vector<uint32_t>{1, 7, 12}));
        CHECK(!v->EraseMetadataKey(*h, 1)); CHECK(v->GetMetadata(*h, 1, got) != 0);
        CHECK(!v->EraseMetadataKey(*h, 12)); CHECK(v->GetMetadata(*h, 12, got) != 0);
        CHECK(!v->GetMetadata(*h, 7, got) && got.size() == 16 && !memcmp(got.data(), updated, 16));
        pixels = static_cast<unsigned char *>(v->Mmap(*h)); CHECK(pixels);
        CHECK(!v->InvalidateCache(*h));
        for (size_t i = 0; i < pixelBytes; ++i) CHECK(pixels[i] == 0xa7);
        CHECK(!v->FlushCache(*h)); CHECK(!v->Unmap(*h));
        printf("ALPHA_METADATA_PASS format=%u pixelBytes=%zu size=%d\n", format, pixelBytes, h->size);
        v->FreeMem(*h);
    }
    BufferHandle *blob = nullptr; CHECK(!v->AllocMem({8192, 1, 0x9, 38, 0}, blob) && blob);
    CHECK(blob->size == 8192 && blob->stride == 8192);
    CHECK(v->SetMetadata(*blob, 1, std::vector<uint8_t>(16)) != 0);
    v->FreeMem(*blob); destroy(v); dlclose(so);
    puts("ALPHA_METADATA_CONTRACT=0 cross_process=1 pixel_guards=1 unknown_rejected=1 blob_unchanged=1");
}
