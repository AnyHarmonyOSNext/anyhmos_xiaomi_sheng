/* Exercise original OHOS HDI implementation, watcher, H4 and callback path. */
#include "bluetooth/hci/v1_0/ihci_interface.h"
#include "bluetooth/hci/v1_0/ihci_callback.h"
#include <cstdio>
#include <atomic>
#include <dlfcn.h>
#include <unistd.h>
#include <signal.h>
#include <ucontext.h>
namespace B=OHOS::HDI::Bluetooth::Hci::V1_0;
static std::atomic<int> initialized{-1};
static std::atomic<int> received{0};
static void crash(int sig,siginfo_t *,void *raw)
{
    auto u=static_cast<ucontext_t *>(raw);Dl_info info{},lr{};
    dladdr(reinterpret_cast<void *>(u->uc_mcontext.pc),&info);
    dladdr(reinterpret_cast<void *>(u->uc_mcontext.regs[30]),&lr);
    printf("BT_HDI_SIGNAL=%d library=%s offset=%llx lr_library=%s lr_offset=%llx\n",sig,
        info.dli_fname?info.dli_fname:"?",(unsigned long long)(u->uc_mcontext.pc-(uintptr_t)info.dli_fbase),
        lr.dli_fname?lr.dli_fname:"?",(unsigned long long)(u->uc_mcontext.regs[30]-(uintptr_t)lr.dli_fbase));
    _exit(100+sig);
}
class Callback final:public B::IHciCallback {
public:
    int32_t OnInited(B::BtStatus status)override{initialized.store(static_cast<int>(status));printf("BT_ORIGINAL_HDI_INIT_CALLBACK=%d\n",int(status));return 0;}
    int32_t OnReceivedHciPacket(B::BtType type,const std::vector<uint8_t>& data)override{
        printf("BT_ORIGINAL_HDI_RX type=%d bytes=",int(type));for(auto b:data)printf("%02x",b);putchar('\n');
        if(data.size()>=6 && data[0]==0x0e && data[3]==1 && data[4]==0x10 && data[5]==0)received.store(1);
        return 0;
    }
};
int main()
{
    setbuf(stdout,nullptr);alarm(35);
    struct sigaction sa{};sa.sa_flags=SA_SIGINFO;sa.sa_sigaction=crash;
    sigaction(SIGTRAP,&sa,nullptr);sigaction(SIGSEGV,&sa,nullptr);sigaction(SIGABRT,&sa,nullptr);
    puts("BT_HDI_STAGE=load_adapter");
    if(!dlopen("/data/local/tmp/libbt_vendor_sheng_v136.so",RTLD_NOW|RTLD_GLOBAL))return 10;
    puts("BT_HDI_STAGE=load_proxy");
    void *proxy=dlopen("libbluetooth_hci_proxy_1.0.z.so",RTLD_NOW|RTLD_GLOBAL);
    puts("BT_HDI_STAGE=load_stub");
    void *stub=dlopen("/vendor/lib64/libbluetooth_hci_stub_1.0.z.so",RTLD_NOW|RTLD_GLOBAL);
    puts("BT_HDI_STAGE=load_service");
    void *lib=dlopen("/vendor/lib64/libhci_interface_service_1.0.z.so",RTLD_NOW|RTLD_GLOBAL);
    if(!proxy || !stub || !lib){printf("BT_HDI_LOAD_ERROR=%s\n",dlerror());return 11;}
    auto get=reinterpret_cast<OHOS::sptr<B::IHciInterface> (*)(bool)>(dlsym(proxy,"_ZN4OHOS3HDI9Bluetooth3Hci4V1_013IHciInterface3GetEb"));
    if(!get)return 12;
    puts("BT_HDI_STAGE=get_original_binder_proxy");
    OHOS::sptr<B::IHciInterface> hci=get(false);if(!hci)return 18;
    puts("BT_HDI_STAGE=create_callback");OHOS::sptr<B::IHciCallback> cb=new Callback();
    puts("BT_HDI_STAGE=initialize");
    int rc=hci->Init(cb);printf("BT_ORIGINAL_HDI_INIT_RC=%d\n",rc);
    if(rc)return 13;
    for(int i=0;i<20 && initialized.load()<0;i++)usleep(100000);
    if(initialized.load()!=0){hci->Close();return 14;}
    rc=hci->SendHciPacket(B::BtType::HCI_CMD,{0x01,0x10,0});
    printf("BT_ORIGINAL_HDI_SEND_RC=%d\n",rc);
    for(int i=0;i<30 && !received.load();i++)usleep(100000);
    printf("BT_ORIGINAL_HDI_REAL_REPLY=%d\n",received.load());
    hci->Close();_exit(received.load() && !rc?0:15);
}
