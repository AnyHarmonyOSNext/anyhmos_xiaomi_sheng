// Real DMA-heap allocation and shared crop round-trip across a process boundary.
#include "idisplay_buffer_vdi.h"
#include <cstdio>
#include <cstring>
#include <dlfcn.h>
#include <sys/wait.h>
#include <unistd.h>
using namespace OHOS::HDI::Display::Buffer::V1_0;
#define CHECK(x) do { if (!(x)) { printf("FAIL line=%d %s\n", __LINE__, #x); return 1; } } while (0)
int main(int argc, char **argv)
{
    setbuf(stdout, nullptr); alarm(15); CHECK(argc == 2);
    void *so = dlopen(argv[1], RTLD_NOW | RTLD_LOCAL); CHECK(so);
    auto create = (CreateDisplayBufferVdiFunc)dlsym(so, "CreateDisplayBufferVdi");
    auto destroy = (DestroyDisplayBufferVdiFunc)dlsym(so, "DestroyDisplayBufferVdi"); CHECK(create && destroy);
    auto *vdi = create(); CHECK(vdi);
    BufferHandle *h = nullptr;
    CHECK(vdi->AllocMem({64,64,0x2b,24,0}, h) == 0 && h);
    CHECK(h->stride == 128 && h->size == 16384 && !h->reserveFds && !h->reserveInts);
    uint32_t rect[4] = {0,0,64,64};
    std::vector<uint8_t> value(sizeof(rect)); memcpy(value.data(), rect, sizeof(rect));
    CHECK(vdi->SetMetadata(*h, 7, value) == 0);
    const pid_t pid = fork(); CHECK(pid >= 0);
    if (!pid) {
        BufferHandle imported = *h; imported.fd = dup(h->fd); imported.virAddr = nullptr;
        std::vector<uint8_t> got;
        if (imported.fd < 0 || vdi->RegisterBuffer(imported) || vdi->GetMetadata(imported, 7, got) || got != value) _exit(2);
        uint32_t update[4] = {2,4,32,24}; memcpy(value.data(), update, sizeof(update));
        int result = vdi->SetMetadata(imported, 7, value); close(imported.fd); _exit(result ? 3 : 0);
    }
    int status = -1; CHECK(waitpid(pid, &status, 0) == pid && WIFEXITED(status) && WEXITSTATUS(status) == 0);
    std::vector<uint8_t> got; CHECK(vdi->GetMetadata(*h, 7, got) == 0);
    uint32_t update[4] = {2,4,32,24}; CHECK(got.size() == sizeof(update) && !memcmp(got.data(), update, sizeof(update)));
    std::vector<uint32_t> keys; CHECK(vdi->ListMetadataKeys(*h, keys) == 0 && keys == std::vector<uint32_t>{7});
    CHECK(vdi->SetMetadata(*h, 7, std::vector<uint8_t>(8)) != 0);
    rect[2] = 65; memcpy(value.data(), rect, sizeof(rect)); CHECK(vdi->SetMetadata(*h, 7, value) != 0);
    CHECK(vdi->SetMetadata(*h, 1, value) != 0);
    BufferHandle old = *h; old.size -= 4096; CHECK(vdi->GetMetadata(old, 7, value) != 0);
    CHECK(vdi->EraseMetadataKey(*h, 7) == 0 && vdi->GetMetadata(*h, 7, value) != 0);
    CHECK(vdi->ListMetadataKeys(*h, keys) == 0 && keys.empty());
    vdi->FreeMem(*h);
    CHECK(vdi->AllocMem({64,64,0x708,12,0}, h) == 0 && h && h->size == 16384 && h->stride == 256);
    vdi->FreeMem(*h); destroy(vdi); dlclose(so);
    puts("CROP_METADATA_PASS cross_process=1 bounds=1 no_fake_unknown_keys=1 rgb_unchanged=1");
    return 0;
}
