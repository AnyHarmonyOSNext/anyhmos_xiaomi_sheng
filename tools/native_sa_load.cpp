// Bounded activation through the original SAMGR proxy, using its exported
// ISystemAbilityManager adjusting thunks. No service status is fabricated.
#include <cstdio>
#include <cstdlib>
#include <dlfcn.h>
#include <unistd.h>
struct Handle { void *ptr = nullptr; ~Handle() {} };
static_assert(sizeof(Handle) == sizeof(void *));
int main(int argc, char **argv)
{
    if (argc != 2) return 2;
    setvbuf(stdout, nullptr, _IOLBF, 0);
    alarm(8);
    int id = std::atoi(argv[1]);
    if (id <= 0) return 3;
    void *lib = dlopen("libsamgr_proxy.z.so", RTLD_NOW | RTLD_GLOBAL);
    if (!lib) { std::printf("SAMGR_DLOPEN_ERROR=%s\n", dlerror()); return 4; }
    auto get = reinterpret_cast<void *(*)()>(dlsym(lib,
        "_ZN4OHOS26SystemAbilityManagerClient11GetInstanceEv"));
    auto manager = reinterpret_cast<Handle (*)(void *)>(dlsym(lib,
        "_ZN4OHOS26SystemAbilityManagerClient23GetSystemAbilityManagerEv"));
    auto check = reinterpret_cast<Handle (*)(void *, int)>(dlsym(lib,
        "_ZThn112_N4OHOS25SystemAbilityManagerProxy18CheckSystemAbilityEi"));
    auto load = reinterpret_cast<Handle (*)(void *, int, int)>(dlsym(lib,
        "_ZThn112_N4OHOS25SystemAbilityManagerProxy17LoadSystemAbilityEii"));
    if (!get || !manager || !check || !load) return 5;
    auto m = manager(get());
    if (!m.ptr) return 6;
    // The donor's known CheckSystemAbility slot confirms this subobject ABI.
    if ((*reinterpret_cast<void ***>(m.ptr))[5] != reinterpret_cast<void *>(check)) {
        puts("SAMGR_INTERFACE_ABI_MISMATCH=1"); return 7;
    }
    auto before = check(m.ptr, id);
    std::printf("SA_BEFORE id=%d ready=%d\n", id, before.ptr != nullptr);
    auto remote = load(m.ptr, id, 4); // Published API uses seconds.
    std::printf("SA_LOAD id=%d ready=%d\n", id, remote.ptr != nullptr);
    auto after = check(m.ptr, id);
    std::printf("SA_AFTER id=%d ready=%d\n", id, after.ptr != nullptr);
    return remote.ptr && after.ptr ? 0 : 8;
}
