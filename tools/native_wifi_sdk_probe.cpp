// Bounded diagnostics of the donor's own device proxy; no network state mocked.
#include <cstdio>
#include <cstring>
#include <cstdint>
#include <dlfcn.h>
#include <time.h>
#include <unistd.h>
struct Shared { void *ptr = nullptr; void *control = nullptr; ~Shared() {} };
static_assert(sizeof(Shared) == 16);
static long long millis()
{
    timespec t{};
    clock_gettime(CLOCK_MONOTONIC, &t);
    return static_cast<long long>(t.tv_sec)*1000+t.tv_nsec/1000000;
}
int main(int argc, char **argv)
{
    if (argc != 3) return 2;
    alarm(5);
    setvbuf(stdout, nullptr, _IOLBF, 0);
    void *lib = dlopen(argv[1], RTLD_NOW | RTLD_GLOBAL);
    if (!lib) { printf("SDK_DLOPEN_ERROR=%s\n", dlerror()); return 3; }
    auto get = reinterpret_cast<Shared (*)(int, int)>(dlsym(lib,
        "_ZN4OHOS4Wifi10WifiDevice11GetInstanceEii"));
    Dl_info info{};
    if (!get || !dladdr(reinterpret_cast<void *>(get), &info) || !info.dli_fbase) return 4;
    auto base = static_cast<const unsigned char *>(info.dli_fbase);
    const unsigned char entry[] = {0xef,0x01,0x00,0xd0,0xef,0x11,0x41,0xf9};
    const unsigned char check[] = {0xc9,0x16,0x40,0xf9};
    const unsigned char skip[] = {0x1b,0x00,0x00,0x14};
    if (memcmp(base+0x4e628, entry, 8) || memcmp(base+0x4e6e8, check, 4) ||
        memcmp(base+0x4e904, skip, 4)) { puts("SDK_BYTE_GUARD_FAILED=1"); return 5; }
    auto device = get(1120, 0);
    if (!device.ptr) { puts("SDK_DEVICE_NULL=1"); return 6; }
    auto id = reinterpret_cast<int *>(static_cast<char *>(device.ptr)+8);
    if (*id != 1120) { printf("SDK_LAYOUT_UNEXPECTED id=%d\n", *id); return 7; }
    bool absent = strcmp(argv[2], "absent") == 0;
    if (absent) *id = 32767; // Separate diagnostic process; test absent-SA fast return.
    auto query = reinterpret_cast<bool (*)(void *)>(const_cast<unsigned char *>(base)+0x4e628);
    long long start = millis();
    bool ready = query(device.ptr);
    printf("SDK_REAL_PROXY id=%d ready=%d elapsed_ms=%lld uid=%d\n", *id, ready, millis()-start, getuid());
    // Handles retained until exit, avoiding guessed donor destructors.
    return ready != absent ? 0 : 8;
}
