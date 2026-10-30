/* Bounded diagnostic using the generated public WLAN C HDI declarations. */
#define _GNU_SOURCE
#include <dlfcn.h>
#include <stdio.h>
#include <unistd.h>
#include "wlan/v1_3/iwlan_interface.h"

int main(void)
{
    setvbuf(stdout, NULL, _IOLBF, 0);
    alarm(10);
    void *lib = dlopen("libwlan_proxy_1.3.z.so", RTLD_NOW | RTLD_LOCAL);
    if (!lib) { printf("HDI_DLOPEN_ERROR=%s\n", dlerror()); return 2; }
    struct IWlanInterface *(*get)(const char *, bool) = dlsym(lib, "IWlanInterfaceGetInstance");
    void (*release)(struct IWlanInterface *, bool) = dlsym(lib, "IWlanInterfaceRelease");
    if (!get || !release) { puts("HDI_SYMBOLS_MISSING=1"); return 3; }
    struct IWlanInterface *wlan = get("wlan_interface_service", false);
    printf("HDI_PROXY_READY=%d\n", wlan != NULL);
    if (!wlan) return 4;
    int r = wlan->Start(wlan);
    printf("HDI_START=%d\n", r);
    if (!r) {
        uint8_t features[64] = {0};
        uint32_t len = sizeof(features);
        r = wlan->GetSupportFeature(wlan, features, &len);
        printf("HDI_SUPPORT=%d LENGTH=%u STA=%u AP=%u\n", r, len, features[2], features[3]);
        int stopped = wlan->Stop(wlan);
        printf("HDI_STOP=%d\n", stopped);
        if (!r) r = stopped;
    }
    release(wlan, false);
    puts("HDI_RELEASED=1");
    return r ? 5 : 0;
}
