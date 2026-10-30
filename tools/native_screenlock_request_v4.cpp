// Original no-password screenlock API request with bounded state polling.
#include <atomic>
#include <cstdio>
#include <unistd.h>
#include <pthread.h>
#include <signal.h>
#include <ucontext.h>
#include <fcntl.h>
#include <cstring>
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
static void crash(int sig, siginfo_t* info, void* raw)
{
    auto* u = static_cast<ucontext_t*>(raw);
    dprintf(1,"SCREENLOCK_CRASH signal=%d address=%p pc=%llx lr=%llx sp=%llx\n",sig,info->si_addr,
        (unsigned long long)u->uc_mcontext.pc,(unsigned long long)u->uc_mcontext.regs[30],
        (unsigned long long)u->uc_mcontext.sp);
    int fd=open("/proc/self/maps",O_RDONLY);char data[4096];ssize_t n;
    while(fd>=0&&(n=read(fd,data,sizeof(data)))>0)write(1,data,n);
    _exit(128+sig);
}
int main()
{
    alarm(35);
    if (!freopen("/data/local/tmp/sheng-capture/unlock-request.txt", "w", stdout)) return 2;
    setbuf(stdout, nullptr);
    struct sigaction action{};
    action.sa_sigaction=crash;action.sa_flags=SA_SIGINFO;
    sigaction(SIGSEGV,&action,nullptr);sigaction(SIGILL,&action,nullptr);sigaction(SIGABRT,&action,nullptr);
    auto manager = ScreenLockManager::GetInstance();
    if (!manager) return 3;
    bool deviceLocked = true;
    int check = manager->IsDeviceLocked(100, deviceLocked);
    bool secure = manager->GetSecure();
    std::printf("SCREENLOCK_CHECK result=%d deviceLocked=%d secure=%d\n", check, deviceLocked, secure);
    if (check != E_SCREENLOCK_OK || deviceLocked || secure) return 5;
    bool forceCallback=access("/data/local/tmp/sheng-capture/screenlock-callback-test",F_OK)==0;
    bool locked = manager->IsScreenLocked();
    std::printf("SCREENLOCK_REQUEST uid=%d before=%d\n", getuid(), locked);
    if (!locked && !forceCallback) {
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
    if (forceCallback) {
        for(unsigned i=0;i<25&&callback->result.load()==-999;++i)sleep(1);
        std::printf("SCREENLOCK_CALLBACK_TEST result=%d\n",callback->result.load());
        if(callback->result.load()==-999)return 10;
    }
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
