/* Read-only use of donor battery implementation through official HDI v2.0. */
#include "battery/v2_0/ibattery_interface.h"
#include <cstdio>
#include <dlfcn.h>
#include <cstring>
#include <unistd.h>
namespace B = OHOS::HDI::Battery::V2_0;
int main(int argc, char **argv)
{
    setbuf(stdout, nullptr);
    alarm(12);
    bool remote=argc==2 && !strcmp(argv[1],"--proxy");
    if(argc>1&&!remote) return 1;
    void *lib = dlopen(remote ? "libbattery_proxy_2.0.z.so" :
                      "/vendor/lib64/libbattery_interface_service_2.0.z.so", RTLD_NOW | RTLD_LOCAL);
    if (!lib) { printf("BATTERY_LOAD_ERROR=%s\n", dlerror()); return 2; }
    auto create = reinterpret_cast<B::IBatteryInterface *(*)()>(dlsym(lib, "BatteryInterfaceImplGetInstance"));
    auto get = reinterpret_cast<OHOS::sptr<B::IBatteryInterface> (*)(bool)>(
        dlsym(lib,"_ZN4OHOS3HDI7Battery4V2_017IBatteryInterface3GetEb"));
    if ((!remote&&!create)||(remote&&!get)) { puts("BATTERY_FACTORY_OR_PROXY_SYMBOL_MISSING"); return 3; }
    // The donor owns background threads. Let process exit reclaim this diagnostic instance.
    OHOS::sptr<B::IBatteryInterface> proxy;
    if(remote) proxy=get(false);
    B::IBatteryInterface *battery = remote ? proxy.GetRefPtr() : create();
    if (!battery) { puts("BATTERY_FACTORY_NULL"); return 4; }
    printf("BATTERY_MODE=%s\n",remote?"original_binder_proxy":"original_implementation");
    int capacity=-999, voltage=-999, temperature=-999, now=-999;
    int a=battery->GetCapacity(capacity), b=battery->GetVoltage(voltage);
    int c=battery->GetTemperature(temperature), d=battery->GetCurrentNow(now);
    printf("BATTERY_ORIGINAL capacity=%d rc=%d voltage=%d rc=%d temperature=%d rc=%d current=%d rc=%d\n",
           capacity,a,voltage,b,temperature,c,now,d);
    B::BatteryInfo info{};
    int rc=battery->GetBatteryInfo(info);
    printf("BATTERY_INFO rc=%d capacity=%d voltage=%d temperature=%d health=%d plugged=%d charge=%d present=%d technology=%s current=%d total=%d remain=%d uevent=%s\n",
           rc,info.capacity,info.voltage,info.temperature,info.healthState,info.pluggedType,
           info.chargeState,int(info.present),info.technology.c_str(),info.curNow,info.totalEnergy,
           info.remainEnergy,info.uevent.c_str());
    return a || b || c || d || rc || capacity<0 || capacity>100 ? 5 : 0;
}
