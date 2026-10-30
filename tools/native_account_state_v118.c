/* Read-only donor account API queries. No credential or account state writes. */
#include <stdbool.h>
#include <stdio.h>
#include <unistd.h>
#include <dlfcn.h>

int main(int argc, char **argv)
{
    (void)argv;
    alarm(8);
    setbuf(stdout, NULL);
    /* Query account100 through the API's own-account read path, without
     * impersonating a privileged permission token or changing account data. */
    if (argc == 2 && getuid() == 0) {
        if (setgid(20000000) || setuid(20000000)) return 4;
    }
    printf("ACCOUNT_STATE_READONLY uid=%d\n", getuid());
    void *lib = dlopen("libos_account_innerkits.z.so", RTLD_NOW | RTLD_LOCAL);
    if (!lib) { puts(dlerror()); return 2; }
    int (*verified)(int, bool *) = dlsym(lib,
        "_ZN4OHOS9AccountSA16OsAccountManager19IsOsAccountVerifiedEiRb");
    int (*active)(int, bool *) = dlsym(lib,
        "_ZN4OHOS9AccountSA16OsAccountManager18IsOsAccountActivedEiRb");
    int (*foreground)(int *) = dlsym(lib,
        "_ZN4OHOS9AccountSA16OsAccountManager29GetForegroundOsAccountLocalIdERi");
    if (!verified || !active || !foreground) return 3;
    int id = -1;
    puts("QUERY_FOREGROUND");
    int ret = foreground(&id);
    printf("FOREGROUND ret=%d user=%d\n", ret, id);
    bool value = false;
    puts("QUERY_VERIFIED_100");
    ret = verified(100, &value);
    printf("VERIFIED user=100 ret=%d value=%d\n", ret, value);
    value = false;
    puts("QUERY_ACTIVE_100");
    ret = active(100, &value);
    printf("ACTIVE user=100 ret=%d value=%d\n", ret, value);
    return 0;
}
