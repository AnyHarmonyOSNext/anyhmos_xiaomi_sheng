/* Test the unmodified donor HAL through its published IWiFi API. */
#define _GNU_SOURCE
#include <dlfcn.h>
#include <stdio.h>
#include <stdint.h>
#include "wifi_hal.h"

int main(void)
{
    setvbuf(stdout, NULL, _IOLBF, 0);
    void *library = dlopen("/vendor/lib64/libwifi_hal.z.so", RTLD_NOW | RTLD_LOCAL);
    if (!library) { printf("HAL_DLOPEN_ERROR=%s\n", dlerror()); return 2; }
    int32_t (*construct)(struct IWiFi **) = dlsym(library, "WifiConstruct");
    int32_t (*destruct)(struct IWiFi **) = dlsym(library, "WifiDestruct");
    if (!construct || !destruct) return 3;
    struct IWiFi *wifi = NULL;
    int r = construct(&wifi); printf("HAL_CONSTRUCT=%d\n", r);
    if (r || !wifi || !wifi->start || !wifi->stop || !wifi->getSupportFeature) return 4;
    r = wifi->start(wifi); printf("HAL_START=%d\n", r);
    if (!r) {
        uint8_t supported[64] = {0};
        int got = wifi->getSupportFeature(supported, sizeof(supported));
        printf("HAL_GET_SUPPORT=%d STA=%u AP=%u P2P_CLIENT=%u P2P_GO=%u\n",
            got, supported[2], supported[3], supported[8], supported[9]);
        int stopped = wifi->stop(wifi); printf("HAL_STOP=%d\n", stopped);
        if (got) r = got; else if (stopped) r = stopped;
    }
    int destroyed = destruct(&wifi); printf("HAL_DESTRUCT=%d\n", destroyed);
    dlclose(library);
    return r || destroyed ? 5 : 0;
}
