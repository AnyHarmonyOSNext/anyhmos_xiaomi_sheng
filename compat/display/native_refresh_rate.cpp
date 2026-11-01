#include <cerrno>
#include <cstdint>
#include <cstdio>
#include <cstdlib>
#include <cstring>
#include <dlfcn.h>
#include <unistd.h>

int main(int argc, char **argv)
{
    char serviceOption[16]{}, serviceValue[16]{}, extra;
    char *serviceArgs[]{argv[0], serviceOption, serviceValue};
    // 从原生服务请求文件读取参数，记录接口调用结果
    if (argc == 1) {
        FILE *request = fopen("/data/local/tmp/sheng-refresh-request.txt", "re");
        if (!request) return 2;
        int fields = fscanf(request, "%15s %15s %c", serviceOption, serviceValue, &extra);
        fclose(request);
        if (fields != 2) return 2;
        if (!freopen("/data/local/tmp/sheng-refresh-result.txt", "ae", stdout) ||
            !freopen("/data/local/tmp/sheng-refresh-result.txt", "ae", stderr)) return 2;
        argc = 3; argv = serviceArgs;
    }
    if (argc != 3 || (strcmp(argv[1], "--mode") && strcmp(argv[1], "--policy"))) {
        fprintf(stderr, "Usage: native_refresh_rate --mode ID | --policy {-1|1|2}\n");
        return 2;
    }
    char *end = nullptr; errno = 0;
    long value = strtol(argv[2], &end, 10);
    bool policy = !strcmp(argv[1], "--policy");
    if (errno || !*argv[2] || *end || (policy ? value != -1 && value != 1 && value != 2 :
        value < 0 || value > UINT32_MAX)) return 2;
    alarm(15); setbuf(stdout, nullptr);
    // 使用原生渲染服务接口更新模式，保持系统与硬件状态同步
    void *library = dlopen("librender_service_client.z.so", RTLD_NOW | RTLD_LOCAL);
    if (!library) { fprintf(stderr, "%s\n", dlerror()); return 3; }
    auto instance = reinterpret_cast<void *(*)()>(dlsym(library,
        "_ZN4OHOS5Rosen12RSInterfaces11GetInstanceEv"));
    auto screen = reinterpret_cast<uint64_t (*)(void *)>(dlsym(library,
        "_ZN4OHOS5Rosen12RSInterfaces18GetDefaultScreenIdEv"));
    if (!instance || !screen) return 4;
    void *client = instance();
    if (!client) return 4;
    if (policy) {
        auto apply = reinterpret_cast<void (*)(void *, int32_t)>(dlsym(library,
            "_ZN4OHOS5Rosen12RSInterfaces18SetRefreshRateModeEi"));
        if (!apply) return 4;
        apply(client, value);
        printf("REFRESH_POLICY_REQUEST policy=%ld\n", value);
    } else {
        uint64_t id = screen(client);
        if (id == UINT64_MAX) { fprintf(stderr, "Default screen unavailable\n"); return 5; }
        auto apply = reinterpret_cast<uint32_t (*)(void *, uint64_t, uint32_t)>(dlsym(library,
            "_ZN4OHOS5Rosen12RSInterfaces19SetScreenActiveModeEmj"));
        if (!apply) return 4;
        uint32_t result = apply(client, id, value);
        printf("REFRESH_MODE_REQUEST screen=%llu id=%ld result=%u\n",
            (unsigned long long)id, value, result);
        if (result) return 6;
    }
    return 0;
}
