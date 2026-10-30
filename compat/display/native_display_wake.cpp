// Original DMS calls in FSM order: begin -> display state -> hardware power -> end.
// Calling SetDisplayState after power-on has already completed instead leaves
// this donor FSM in WAIT_LOCK_SCREEN_IND, breaking subsequent power-key events.
#include <cstdio>
#include <cstdint>
#include <dlfcn.h>
#include <functional>
#include <atomic>
#include <unistd.h>
int main()
{
    char log[128];
    snprintf(log, sizeof(log), "/data/local/tmp/sheng-capture/dms-wake-%d.txt", getpid());
    if (!freopen(log, "wx", stdout)) return 10;
    setbuf(stdout, nullptr);
    alarm(15);
    void *lib = dlopen("libdm.z.so", RTLD_NOW | RTLD_LOCAL);
    if (!lib) { puts(dlerror()); return 2; }
    auto dm = reinterpret_cast<void *(*)()>(dlsym(lib, "_ZN4OHOS5Rosen14DisplayManager11GetInstanceEv"));
    auto sm = reinterpret_cast<void *(*)()>(dlsym(lib, "_ZN4OHOS5Rosen13ScreenManager11GetInstanceEv"));
    auto begin = reinterpret_cast<bool (*)(void *, uint32_t)>(dlsym(lib,
        "_ZN4OHOS5Rosen14DisplayManager11WakeUpBeginENS0_22PowerStateChangeReasonE"));
    auto power = reinterpret_cast<bool (*)(void *, uint32_t, uint32_t)>(dlsym(lib,
        "_ZN4OHOS5Rosen13ScreenManager20SetScreenPowerForAllENS0_16ScreenPowerStateENS0_22PowerStateChangeReasonE"));
    auto state = reinterpret_cast<bool (*)(void *, uint32_t, std::function<void(uint32_t)>)>(dlsym(lib,
        "_ZN4OHOS5Rosen14DisplayManager15SetDisplayStateENS0_12DisplayStateENSt3__h8functionIFvS2_EEE"));
    auto end = reinterpret_cast<bool (*)(void *)>(dlsym(lib, "_ZN4OHOS5Rosen14DisplayManager9WakeUpEndEv"));
    if (!dm || !sm || !begin || !power || !state || !end) return 3;
    void *d = dm(), *s = sm();
    if (!d || !s) return 4;
    bool b = begin(d, 0);
    printf("DMS_WAKE_BEGIN=%d\n", b);
    if (!b) return 5;
    std::atomic<unsigned> observed{0};
    bool a = state(d, 2, [&observed](uint32_t value) { observed.store(value); });
    printf("DMS_DISPLAY_STATE_ON_BEFORE_POWER=%d\n", a);
    bool p = power(s, 0, 0);
    printf("DMS_SCREEN_POWER_ON=%d\n", p);
    bool e = end(d);
    printf("DMS_WAKE_END=%d\n", e);
    for (unsigned i = 0; a && observed.load() != 2 && i < 40; ++i) usleep(50000);
    printf("DMS_DISPLAY_STATE_CALLBACK=%u\n", observed.load());
    return b && p && a && e ? 0 : 6;
}
