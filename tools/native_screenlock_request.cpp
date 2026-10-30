// Ask the original screenlock service to dismiss the no-password test lockscreen.
// Authentication, focus and token checks remain in the original framework.
#include <atomic>
#include <cstdio>
#include <unistd.h>
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
    alarm(12);
    if (!freopen("/data/local/tmp/sheng-capture/unlock-request.txt", "w", stdout)) return 2;
    setbuf(stdout, nullptr);
    auto manager = ScreenLockManager::GetInstance();
    if (!manager) return 3;
    bool deviceLocked = true;
    int check = manager->IsDeviceLocked(100, deviceLocked);
    bool secure = manager->GetSecure();
    std::printf("SCREENLOCK_CHECK result=%d deviceLocked=%d secure=%d\n", check, deviceLocked, secure);
    if (check != E_SCREENLOCK_OK || deviceLocked || secure) return 5;
    std::printf("SCREENLOCK_REQUEST uid=%d before=%d\n", getuid(), manager->IsScreenLocked());
    sptr<Callback> callback = new Callback;
    int ret = manager->Unlock(Action::UNLOCKSCREEN, callback);
    std::printf("SCREENLOCK_REQUEST ret=%d\n", ret);
    for (unsigned i = 0; ret == E_SCREENLOCK_OK && callback->result.load() == -999 && i < 80; ++i) usleep(100000);
    std::printf("SCREENLOCK_REQUEST callback=%d after=%d\n", callback->result.load(), manager->IsScreenLocked());
    return ret == E_SCREENLOCK_OK ? 0 : 4;
}
