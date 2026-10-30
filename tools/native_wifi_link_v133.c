/* Read the original Wi-Fi SDK's public C API without changing network state.
 * Header: communication_wifi OpenHarmony-6.0-Release, abbb443cdd943a393b3d0b95d21df67262b7610e.
 * The donor's conversion stores at offsets 40..80 were checked against this header.
 * Never print SSID, BSSID, IP, or credentials.
 */
#include <dlfcn.h>
#include <fcntl.h>
#include <stddef.h>
#include <stdio.h>
#include <string.h>
#include <unistd.h>
#include "wifi_linked_info.h"

_Static_assert(sizeof(WifiLinkedInfo) == 88, "C linked-info size changed");
_Static_assert(offsetof(WifiLinkedInfo, rssi) == 40, "RSSI ABI changed");
_Static_assert(offsetof(WifiLinkedInfo, wifiStandard) == 64, "standard ABI changed");
_Static_assert(offsetof(WifiLinkedInfo, txLinkSpeed) == 80, "speed ABI changed");

int main(int argc, char **argv)
{
    if (argc == 2 && !strcmp(argv[1], "--service")) {
        int fd = open("/data/local/tmp/sheng-wifi-link-v133.txt",
            O_WRONLY | O_TRUNC | O_NOFOLLOW);
        if (fd < 0) return 6;
        if (dup2(fd, STDOUT_FILENO) < 0 || dup2(fd, STDERR_FILENO) < 0) return 7;
        close(fd);
    } else if (argc != 1) return 8;
    setvbuf(stdout, NULL, _IOLBF, 0);
    alarm(5);
    void *library = dlopen("/system/lib64/platformsdk/libwifi_sdk.z.so", RTLD_NOW | RTLD_GLOBAL);
    if (!library) { printf("WIFI_LINK_DLOPEN_ERROR=%s\n", dlerror()); return 2; }
    int (*get)(WifiLinkedInfo *) = dlsym(library, "GetLinkedInfo");
    if (!get) { puts("WIFI_LINK_SYMBOL_MISSING=1"); return 3; }
    struct { WifiLinkedInfo info; unsigned char guard[64]; } result;
    memset(&result, 0, sizeof(result));
    memset(result.guard, 0xa5, sizeof(result.guard));
    int rc = get(&result.info);
    for (size_t i = 0; i < sizeof(result.guard); ++i) {
        if (result.guard[i] != 0xa5) { puts("WIFI_LINK_GUARD_FAILED=1"); return 4; }
    }
    printf("WIFI_LINK_PUBLIC_C rc=%d uid=%u guard=ok\n", rc, (unsigned)getuid());
    if (rc) return 5;
    printf("WIFI_LINK_REAL connected=%d frequency=%d band=%d rssi=%d standard=%u max_rx=%d max_tx=%d rx=%d tx=%d\n",
        result.info.connState, result.info.frequency, result.info.band, result.info.rssi,
        result.info.wifiStandard, result.info.maxSupportedRxLinkSpeed,
        result.info.maxSupportedTxLinkSpeed, result.info.rxLinkSpeed, result.info.txLinkSpeed);
    return 0;
}
