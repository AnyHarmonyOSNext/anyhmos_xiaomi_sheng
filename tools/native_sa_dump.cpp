// One-shot read-only diagnostics through the donor's original samgr and IPC Dump.
// Carrier matches the donor sptr's AArch64 indirect-return ABI. References are
// intentionally retained until this bounded process exits; no guessed destructor.
#include <cstdio>
#include <cstdlib>
#include <dlfcn.h>
#include <fcntl.h>
#include <string>
#include <unistd.h>
#include <vector>
struct Handle { void *ptr = nullptr; ~Handle() {} };
static_assert(sizeof(Handle) == sizeof(void *));
int main(int argc, char **argv)
{
    if (argc < 3) return 2;
    const int id = std::atoi(argv[1]);
    if (id <= 0) return 3;
    void *samgr = dlopen("libsamgr_proxy.z.so", RTLD_NOW | RTLD_GLOBAL);
    void *ipc = dlopen("libipc_single.z.so", RTLD_NOW | RTLD_GLOBAL);
    if (!samgr || !ipc) { std::fprintf(stderr, "dlopen: %s\n", dlerror()); return 4; }
    auto get = reinterpret_cast<void *(*)()>(dlsym(samgr, "_ZN4OHOS26SystemAbilityManagerClient11GetInstanceEv"));
    auto manager = reinterpret_cast<Handle (*)(void *)>(dlsym(samgr, "_ZN4OHOS26SystemAbilityManagerClient23GetSystemAbilityManagerEv"));
    auto dump = reinterpret_cast<int (*)(void *, int, const std::vector<std::u16string> &)>(dlsym(ipc,
        "_ZN4OHOS14IPCObjectProxy4DumpEiRKNSt3__h6vectorINS1_12basic_stringIDsNS1_11char_traitsIDsEENS1_9allocatorIDsEEEENS6_IS8_EEEE"));
    if (!get || !manager || !dump) return 5;
    auto m = manager(get());
    if (!m.ptr) return 6;
    auto check = reinterpret_cast<Handle (*)(void *, int)>((*reinterpret_cast<void ***>(m.ptr))[5]);
    auto remote = check(m.ptr, id);
    if (!remote.ptr) { std::fprintf(stderr, "SA %d unavailable\n", id); return 7; }
    std::vector<std::u16string> args;
    for (int i = 3; i < argc; ++i) {
        std::u16string s;
        for (const unsigned char *p = reinterpret_cast<unsigned char *>(argv[i]); *p; ++p) {
            if (*p >= 128) return 8;
            s.push_back(*p);
        }
        args.emplace_back(std::move(s));
    }
    const int fd = open(argv[2], O_WRONLY | O_CREAT | O_EXCL | O_CLOEXEC, 0600);
    if (fd < 0) { std::perror("output"); return 9; }
    const int result = dump(remote.ptr, fd, args);
    close(fd);
    std::fprintf(stderr, "NATIVE_SA_DUMP sa=%d result=%d args=%zu\n", id, result, args.size());
    return result == 0 ? 0 : 10;
}
