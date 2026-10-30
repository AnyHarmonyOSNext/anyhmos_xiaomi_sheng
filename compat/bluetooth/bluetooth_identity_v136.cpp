/* Read chipset identity through original303 HAL logic; never power it on. */
#include <stdio.h>
#include <stdarg.h>
#include <unistd.h>
#include <dlfcn.h>
#include <string>
#include <cstdint>

extern "C" int property_set(const char *key,const char *value)
{
    printf("BT_IDENTITY_PROPERTY_WRITE_BLOCKED key=%s value=%s\n",key,value);
    return -1;
}
extern "C" int __android_log_print(int priority,const char *tag,const char *fmt,...)
{
    printf("BT_LOG[%d][%s] ",priority,tag);
    va_list args;va_start(args,fmt);int n=vprintf(fmt,args);va_end(args);
    putchar('\n');return n;
}
static int run(int,char **,char **)
{
    setvbuf(stdout,nullptr,_IOLBF,0);alarm(6);
    void *lib=dlopen("/hmos-root/data/local/tmp/bt-backend-v136/lib64/android.hardware.bluetooth@1.0-impl-qti.so",RTLD_NOW|RTLD_LOCAL);
    if(!lib){printf("BT_DLOPEN_ERROR=%s\n",dlerror());return 11;}
    using Default=std::string (*)();
    auto detect=reinterpret_cast<Default>(dlsym(lib,"_Z26setVendorPropertiesDefaultv"));
    if(!detect)return 12;
    std::string name=detect();printf("BT_ORIGINAL_DETECTED_SOC=%s\n",name.c_str());
    void *soc=dlopen("libsoc_helper.so",RTLD_NOW|RTLD_LOCAL);
    if(!soc){printf("BT_SOC_HELPER_ERROR=%s\n",dlerror());return 13;}
    // Disassembled original function writes exactly two int32s through x0.
    struct SocInfo { int32_t first,second; } info={-1,-1};
    using GetInfo=void (*)(SocInfo *);
    auto get=reinterpret_cast<GetInfo>(dlsym(soc,"get_soc_info"));
    if(!get)return 14;
    get(&info);printf("BT_ORIGINAL_SOC_INFO=%d,%d\n",info.first,info.second);
    puts("BT_IDENTITY_NO_INITIALIZE_POWER_OR_SEND=1");return 0;
}
extern "C" __attribute__((noreturn)) void __libc_init(void *raw,void (*onexit)(void),
    int (*)(int,char **,char **),const void *structors)
{
    using Entry=void (*)(void *,void (*)(void),int (*)(int,char **,char **),const void *);
    auto real=reinterpret_cast<Entry>(dlsym(RTLD_NEXT,"__libc_init"));
    if(real)real(raw,onexit,run,structors);
    _exit(90);
}
