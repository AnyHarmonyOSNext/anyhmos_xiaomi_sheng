/* Original303 Qualcomm HCI load/symbol probe. No initialize/power/send calls. */
#ifndef _GNU_SOURCE
#define _GNU_SOURCE
#endif
#include <stdio.h>
#include <unistd.h>
#include <dlfcn.h>
#include <functional>
#include <cstddef>

static int run(int argc,char **argv,char **envp)
{
    (void)argc;(void)argv;(void)envp;
    setvbuf(stdout,nullptr,_IOLBF,0);alarm(6);
    printf("BT_ANDROID_LIBCPP_CALLBACK_ABI size=%zu align=%zu\n",
        sizeof(std::function<void(bool)>),alignof(std::function<void(bool)>));
    static_assert(sizeof(std::function<void(bool)>)==48,"original libc++ ABI v1");
    static_assert(alignof(std::function<void(bool)>)==16,"original function alignment");
    void *lib=dlopen("/hmos-root/data/local/tmp/bt-backend-v136/lib64/android.hardware.bluetooth@1.0-impl-qti.so",RTLD_NOW|RTLD_LOCAL);
    if (!lib) { printf("BT_ORIGINAL_QTI_DLOPEN_ERROR=%s\n",dlerror());return 11; }
    puts("BT_ORIGINAL_QTI_DLOPEN_OK=1");
    const char *names[]={
        "_ZN7android8hardware9bluetooth4V1_014implementation11DataHandler4InitE12ProtocolTypeNSt3__18functionIFvbEEENS7_IFv13HciPacketTypePKNS0_8hidl_vecIhEEEEE",
        "_ZN7android8hardware9bluetooth4V1_014implementation11DataHandler3GetEv",
        "_ZN7android8hardware9bluetooth4V1_014implementation11DataHandler7CleanUpE12ProtocolType",
        "_ZN7android8hardware9bluetooth4V1_014implementation11DataHandler8SendDataE12ProtocolType13HciPacketTypePKhm"};
    for (const char *name:names) {
        void *symbol=dlsym(lib,name);Dl_info info={};
        if (!symbol || !dladdr(symbol,&info)) { printf("BT_SYMBOL_MISSING=%s\n",name);return 12; }
        printf("BT_ORIGINAL_SYMBOL offset=%#lx name=%s\n",(unsigned long)((char *)symbol-(char *)info.dli_fbase),name);
    }
    puts("BT_READ_ONLY_NO_INITIALIZE_POWER_OR_SEND=1");
    return 0;
}

extern "C" __attribute__((noreturn)) void __libc_init(void *raw_args,void (*onexit)(void),
    int (*original_main)(int,char **,char **),const void *structors)
{
    (void)original_main;
    using Entry=void (*)(void *,void (*)(void),int (*)(int,char **,char **),const void *);
    Entry real=reinterpret_cast<Entry>(dlsym(RTLD_NEXT,"__libc_init"));
    if (real) real(raw_args,onexit,run,structors);
    _exit(90);
}
