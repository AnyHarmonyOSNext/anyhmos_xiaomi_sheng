/* Trace only our bounded diagnostic child and its threads. Never attach to OS services. */
#define _GNU_SOURCE
#include <sys/ptrace.h>
#include <sys/wait.h>
#include <sys/uio.h>
#include <sys/types.h>
#include <elf.h>
#include <signal.h>
#include <unistd.h>
#include <fcntl.h>
#include <errno.h>
#include <stdio.h>
#include <stdlib.h>
#include <stdint.h>

static volatile sig_atomic_t child_pid;

static void timeout_handler(int sig)
{
    if (child_pid > 0) kill(-child_pid, SIGKILL);
    _exit(128+sig);
}

static void crash(pid_t tid, int sig)
{
    struct { uint64_t x[31], sp, pc, pstate; } regs = {0};
    struct iovec iov = { &regs, sizeof(regs) };
    int rc = ptrace(PTRACE_GETREGSET, tid, (void *)NT_PRSTATUS, &iov);
    printf("AUDIO_CRASH_TID=%d SIGNAL=%d REGS_RC=%d PC=0x%llx LR=0x%llx SP=0x%llx\n",
           tid, sig, rc, (unsigned long long)regs.pc,
           (unsigned long long)regs.x[30], (unsigned long long)regs.sp);
    for (unsigned i=0; i<31; i++)
        printf("X%u=0x%llx\n", i, (unsigned long long)regs.x[i]);
    for (unsigned i=0; i<24 && rc == 0; i++) {
        errno = 0;
        long word = ptrace(PTRACE_PEEKDATA, tid, (void *)(regs.sp+i*8), 0);
        if (errno) break;
        printf("STACK_%u=0x%lx\n", i, word);
    }
    char path[80], buf[4096];
    snprintf(path, sizeof(path), "/proc/%d/maps", tid);
    int fd = open(path, O_RDONLY|O_CLOEXEC);
    puts("AUDIO_CRASH_MAPS_BEGIN");
    fflush(stdout);
    if (fd >= 0) {
        ssize_t n;
        size_t total = 0;
        while (total < 262144 && (n=read(fd, buf, sizeof(buf))) > 0) {
            (void)write(1, buf, (size_t)n);
            total += (size_t)n;
        }
        close(fd);
    }
    puts("AUDIO_CRASH_MAPS_END");
}

int main(int argc, char **argv)
{
    if (argc < 2 || argv[1][0] != '/') return 2;
    setvbuf(stdout, NULL, _IOLBF, 0);
    signal(SIGALRM, timeout_handler);
    signal(SIGTERM, timeout_handler);
    signal(SIGINT, timeout_handler);
    pid_t pid = fork();
    if (pid < 0) return 3;
    if (pid == 0) {
        if (setsid() < 0 || ptrace(PTRACE_TRACEME, 0, 0, 0)) _exit(4);
        raise(SIGSTOP);
        execv(argv[1], argv+1);
        _exit(5);
    }
    child_pid = pid;
    alarm(20);
    int status;
    if (waitpid(pid, &status, 0) != pid || !WIFSTOPPED(status)) return 6;
    unsigned long options = PTRACE_O_TRACECLONE|PTRACE_O_TRACEFORK|PTRACE_O_TRACEVFORK|
                            PTRACE_O_TRACEEXEC|PTRACE_O_EXITKILL;
    if (ptrace(PTRACE_SETOPTIONS, pid, 0, (void *)options)) {
        perror("SETOPTIONS");
        kill(-pid, SIGKILL);
        return 7;
    }
    ptrace(PTRACE_CONT, pid, 0, 0);
    for (;;) {
        pid_t tid = waitpid(-1, &status, __WALL);
        if (tid < 0) { if (errno == EINTR) continue; break; }
        if (WIFEXITED(status) && tid == pid) return WEXITSTATUS(status);
        if (WIFSIGNALED(status) && tid == pid) return 128+WTERMSIG(status);
        if (!WIFSTOPPED(status)) continue;
        int sig = WSTOPSIG(status);
        if (sig == SIGSEGV || sig == SIGABRT || sig == SIGBUS) {
            crash(tid, sig);
            kill(-pid, SIGKILL);
            return 128+sig;
        }
        if (sig == SIGTRAP || sig == SIGSTOP) sig=0;
        ptrace(PTRACE_CONT, tid, 0, (void *)(long)sig);
    }
    return 8;
}
