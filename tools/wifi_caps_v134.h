#ifndef SHENG_WIFI_CAPS_V134_H
#define SHENG_WIFI_CAPS_V134_H
#include <stdint.h>
struct ShengWifiCaps {
    uint32_t ifindex, wiphy;
    unsigned he, eht, records, mask;
};
int ShengReadWifiCaps(const char *ifname, struct ShengWifiCaps *caps);
#endif
