/* Read-only queries through the donor's original MemMgrClient and real IPC. */
#include <dlfcn.h>
#include <stdio.h>
#include <unistd.h>
#include <time.h>
#include <string.h>
#include <grp.h>
#include <fcntl.h>

int main(int argc, char **argv)
{
    alarm(12);
    if (argc == 2 && strcmp(argv[1], "--system-uid") == 0) {
        if (getuid() != 0 || setgroups(0, NULL) || setgid(1000) || setuid(1000)) return 6;
    } else if (argc == 2 && strcmp(argv[1], "--service-output") == 0) {
        int fd = open("/data/local/tmp/sheng-memmgr-readonly.txt", O_WRONLY | O_TRUNC | O_CLOEXEC | O_NOFOLLOW);
        if (fd < 0 || dup2(fd, 1) < 0 || dup2(fd, 2) < 0) return 8;
        close(fd);
    } else if (argc != 1) return 7;
    printf("MEMMGR_READONLY_CALLER uid=%d gid=%d\n", getuid(), getgid());
    void *h = dlopen("libmemmgrclient.z.so", RTLD_NOW | RTLD_GLOBAL);
    if (!h) { fprintf(stderr, "dlopen=%s\n", dlerror()); return 2; }
    void *(*instance)(void) = dlsym(h, "_ZN4OHOS6Memory12MemMgrClient11GetInstanceEv");
    int (*available)(void *, int *) = dlsym(h, "_ZN4OHOS6Memory12MemMgrClient18GetAvailableMemoryERi");
    int (*total)(void *, int *) = dlsym(h, "_ZN4OHOS6Memory12MemMgrClient14GetTotalMemoryERi");
    int (*priority)(void *, int, int *) = dlsym(h, "_ZN4OHOS6Memory12MemMgrClient23GetReclaimPriorityByPidEiRi");
    if (!instance || !available || !total || !priority) return 3;
    void *c = instance();
    if (!c) return 4;
    struct timespec start, end;
    int a = -1, t = -1, p = -1;
    clock_gettime(CLOCK_MONOTONIC, &start);
    int ar = available(c, &a), tr = total(c, &t), pr = priority(c, getpid(), &p);
    clock_gettime(CLOCK_MONOTONIC, &end);
    double elapsed = end.tv_sec - start.tv_sec + (end.tv_nsec - start.tv_nsec) / 1e9;
    printf("NATIVE_MEMMGR_QUERY available_ret=%d available=%d total_ret=%d total=%d priority_ret=%d priority=%d elapsed=%.6f\n",
           ar, a, tr, t, pr, p, elapsed);
    return ar == 0 && tr == 0 && t > 0 && a > 0 && a <= t ? 0 : 5;
}
