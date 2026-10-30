/* Read-only diagnostic of the original optional CLI service loading deadline. */
#include <dlfcn.h>
#include <stdbool.h>
#include <stdio.h>
#include <time.h>
#include <unistd.h>
int main(void) {
    alarm(8);
    void *lib = dlopen("libcli_tool_client.z.so", RTLD_NOW);
    if (!lib) { printf("dlopen=%s\n", dlerror()); return 2; }
    void *(*instance)(void) = dlsym(lib, "_ZN4OHOS7CliTool16CliToolMGRClient11GetInstanceEv");
    bool (*load)(void *) = dlsym(lib, "_ZN4OHOS7CliTool16CliToolMGRClient21LoadCliToolMgrServiceEv");
    if (!instance || !load) return 3;
    struct timespec a, b;
    clock_gettime(CLOCK_MONOTONIC, &a);
    bool ok = load(instance());
    clock_gettime(CLOCK_MONOTONIC, &b);
    printf("CLI_LOAD_DIAGNOSTIC result=%d elapsed=%.6f\n", ok,
           b.tv_sec - a.tv_sec + (b.tv_nsec-a.tv_nsec)/1e9);
    return 0;
}
