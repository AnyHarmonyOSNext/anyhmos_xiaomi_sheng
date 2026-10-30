// Original no-password screenlock API request with bounded state polling.
#include <atomic>
#include <cstdio>
#include <unistd.h>
#include <pthread.h>
#include "ipc_skeleton.h"
#include "screenlock_manager.h"
#include "screenlock_callback_stub.h"
using namespace OHOS;
using namespace OHOS::ScreenLock;
class Callback final : public ScreenLockCallbackStub {
public:
    std::atomic<int> result{-999};
    void OnCallBack(int32_t value) override { result.store(value); }
};
int main()
{
    alarm(35);
    if (!freopen("/data/local/tmp/sheng-capture/unlock-request.txt", "w", stdout)) return 2;
    setbuf(stdout, nullptr);
    auto manager = ScreenLockManager::GetInstance();
    if (!manager) return 3;
    bool deviceLocked = true;
    int check = manager->IsDeviceLocked(100, deviceLocked);
    bool secure = manager->GetSecure();
    std::printf("SCREENLOCK_CHECK result=%d deviceLocked=%d secure=%d\n", check, deviceLocked, secure);
    if (check != E_SCREENLOCK_OK || deviceLocked || secure) return 5;
    bool locked = manager->IsScreenLocked();
    std::printf("SCREENLOCK_REQUEST uid=%d before=%d\n", getuid(), locked);
    if (!locked) {
        std::puts("SCREENLOCK_VERIFIED after=0 already_unlocked=1");
        return 0;
    }
    if (!IPCSkeleton::SetMaxWorkThreadNum(2)) return 7;
    pthread_t ipcThread;
    if (pthread_create(&ipcThread, nullptr, [](void*) -> void* {
        IPCSkeleton::JoinWorkThread(); return nullptr;
    }, nullptr) != 0) return 8;
    pthread_detach(ipcThread);
    sptr<Callback> callback = new Callback;
    int ret = manager->Unlock(Action::UNLOCKSCREEN, callback);
    std::printf("SCREENLOCK_REQUEST ret=%d\n", ret);
    if (ret != E_SCREENLOCK_OK) return 4;
    // Callback delivery is optional. Query the original authoritative state.
    for (unsigned i = 0; i < 25; ++i) {
        sleep(1);
        locked = manager->IsScreenLocked();
        if (!locked) {
            std::printf("SCREENLOCK_VERIFIED after=0 callback=%d elapsed=%u\n", callback->result.load(), i + 1);
            return 0;
        }
    }
    std::puts("SCREENLOCK_TIMEOUT after=1");
    return 6;
}
