/* Read the original public NDK API; no battery values are supplied by this tool. */
#include "ohbattery_info.h"
#include <dlfcn.h>
#include <stdio.h>
#include <unistd.h>
int main(void)
{
    setbuf(stdout,NULL); alarm(8);
    void *lib=dlopen("libohbattery_info.so",RTLD_NOW|RTLD_LOCAL);
    if(!lib) { printf("BATTERY_NDK_LOAD_ERROR=%s\n",dlerror()); return 2; }
    int32_t (*capacity)(void)=(int32_t (*)(void))dlsym(lib,"OH_BatteryInfo_GetCapacity");
    BatteryInfo_BatteryPluggedType (*plugged)(void)=
        (BatteryInfo_BatteryPluggedType (*)(void))dlsym(lib,"OH_BatteryInfo_GetPluggedType");
    if(!capacity||!plugged) return 3;
    int soc=capacity(),type=plugged();
    printf("BATTERY_PUBLIC_NDK capacity=%d plugged=%d\n",soc,type);
    return soc<0||soc>100||type<0||type>=PLUGGED_TYPE_BUTT ? 4 : 0;
}
