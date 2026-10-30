// Bounded A/B probe for the exact donor's CommitTransaction transport.
// Change only MessageOption::TF_ASYNC -> TF_SYNC. Keep server checks intact.
// PTRACE_POKETEXT creates a private COW page and performs architecture cache maintenance.
#include <errno.h>
#include <fcntl.h>
#include <signal.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/ptrace.h>
#include <sys/wait.h>
#include <unistd.h>

int main(int argc, char **argv)
{
    if (argc != 3 || (strcmp(argv[2], "enable") && strcmp(argv[2], "restore") &&
        strcmp(argv[2], "enable-mem") && strcmp(argv[2], "restore-mem"))) return 2;
    int memory_mode = strstr(argv[2], "-mem") != NULL;
    pid_t pid = (pid_t)strtol(argv[1], NULL, 10);
    if (pid <= 1 || pid == getpid()) return 3;
    alarm(6);
    char path[64], line[1024];
    snprintf(path, sizeof(path), "/proc/%d/maps", pid);
    FILE *maps = fopen(path, "r");
    if (!maps) { perror("maps"); return 4; }
    uintptr_t base = 0;
    while (fgets(line, sizeof(line), maps)) {
        unsigned long start, end, off;
        char perms[8];
        if (strstr(line, "/compat/lib64/librender_service_base.z.so") &&
            sscanf(line, "%lx-%lx %7s %lx", &start, &end, perms, &off) == 4 &&
            off == 0 && perms[0] == 'r') { base = start; break; }
    }
    fclose(maps);
    if (!base) return 5;
    if (!memory_mode && ptrace(PTRACE_ATTACH, pid, 0, 0) < 0) { perror("attach"); return 6; }
    int status, result = 7, fd = -1;
    if (!memory_mode && (waitpid(pid, &status, 0) != pid || !WIFSTOPPED(status))) goto detach;
    // Guard: add x0,sp,#24; mov w1,#1 (or #0); bl MessageOption::SetFlags.
    uint32_t guard[3] = {0};
    snprintf(path, sizeof(path), "/proc/%d/mem", pid);
    fd = open(path, (memory_mode ? O_RDWR : O_RDONLY) | O_CLOEXEC);
    if (fd < 0) { perror("mem"); goto detach; }
    ssize_t n = pread(fd, guard, sizeof(guard), (off_t)(base + 0x88bdb0));
    if (n != sizeof(guard) || guard[0] != 0x910063e0 || guard[2] != 0x94013216 ||
        (guard[1] != 0x52800021 && guard[1] != 0x52800001)) {
        fprintf(stderr, "guard mismatch n=%zd %08x %08x %08x\n", n, guard[0], guard[1], guard[2]);
        result = 8; goto detach;
    }
    uint32_t before = guard[1];
    uint32_t desired = !strncmp(argv[2], "enable", 6) ? 0x52800001 : 0x52800021;
    if (guard[1] != desired) {
        uint64_t word = ((uint64_t)desired << 32) | guard[0];
        if (memory_mode) {
            // proc_mem writes use the same forced COW/copy_to_user_page path.
            // The single aligned instruction does not change control flow.
            if (pwrite(fd, &desired, sizeof(desired), (off_t)(base + 0x88bdb4)) != sizeof(desired) ||
                pread(fd, guard, sizeof(guard), (off_t)(base + 0x88bdb0)) != sizeof(guard) ||
                guard[1] != desired) { perror("mem write/readback"); result = 9; goto detach; }
        } else {
        if (ptrace(PTRACE_POKETEXT, pid, (void *)(base + 0x88bdb0), (void *)word) < 0) {
            perror("poke"); result = 9; goto detach;
        }
        errno = 0;
        long check = ptrace(PTRACE_PEEKTEXT, pid, (void *)(base + 0x88bdb0), 0);
        if (errno || (uint64_t)check != word) { result = 10; goto detach; }
        }
    }
    printf("RS_COMMIT_TRANSPORT pid=%d base=%lx old=%08x new=%08x verified=1\n",
        pid, (unsigned long)base, before, desired);
    result = 0;
detach:
    if (fd >= 0) close(fd);
    if (!memory_mode && ptrace(PTRACE_DETACH, pid, 0, 0) < 0) { perror("detach"); return 11; }
    return result;
}
