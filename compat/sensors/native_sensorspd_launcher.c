#define _GNU_SOURCE 1
#include <errno.h>
#include <fcntl.h>
#include <grp.h>
#include <linux/capability.h>
#include <sys/file.h>
#include <sys/mount.h>
#include <sys/stat.h>
#include <limits.h>
#include <signal.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/prctl.h>
#include <sys/syscall.h>
#include <sys/wait.h>
#include <time.h>
#include <unistd.h>

static volatile sig_atomic_t stop_requested;

static void requested_stop(int signal_number)
{
    stop_requested = signal_number;
}

static void child_changed(int signal_number)
{
    (void)signal_number;
}

static int failed(const char *step)
{
    fprintf(stderr, "SENSORSPD_SERVICE_ERROR step=%s errno=%d\n", step, errno);
    return 70;
}

static long long milliseconds(void)
{
    struct timespec value;
    if (clock_gettime(CLOCK_MONOTONIC, &value)) return -1;
    return (long long)value.tv_sec * 1000 + value.tv_nsec / 1000000;
}

static void pause_tick(void)
{
    struct timespec value = {0, 50000000};
    nanosleep(&value, NULL);
}

/* 保留退出子进程的 PID，完成自有锁清理后再回收 */
static int child_status(pid_t child)
{
    siginfo_t info = {0};
    int result = waitid(P_PID, (id_t)child, &info, WEXITED | WNOHANG | WNOWAIT);
    if (!result) return info.si_pid == child;
    if (errno == EINTR) return 0;
    return -1;
}

static int wait_owned_child(pid_t child, long long duration)
{
    long long start = milliseconds();
    if (start < 0) return -1;
    do {
        int result = child_status(child);
        if (result) return result;
        pause_tick();
        long long now = milliseconds();
        if (now < 0) return -1;
        if (now - start >= duration) return 0;
    } while (1);
}

static int lock_separator(char value)
{
    return value == ' ' || value == '\t' || value == '\n' ||
        value == '\r' || value == '\v' || value == '\f';
}

/* 按完整名称匹配活动锁，不接受前缀或其他进程的锁 */
static int count_lock_name(const char *list, const char *name)
{
    size_t length = strlen(name);
    int count = 0;
    while (*list) {
        while (*list && lock_separator(*list)) ++list;
        const char *begin = list;
        while (*list && !lock_separator(*list)) ++list;
        if ((size_t)(list - begin) == length && !memcmp(begin, name, length)) ++count;
    }
    return count;
}

static char *read_active_locks(void)
{
    FILE *file = fopen("/sys/power/wake_lock", "re");
    if (!file) return NULL;
    char *line = NULL;
    size_t capacity = 0;
    ssize_t length = getline(&line, &capacity, file);
    int error = errno;
    if (length < 0 && !ferror(file)) {
        free(line);
        line = strdup("");
        if (!line) error = ENOMEM;
    } else if (length < 0) {
        free(line);
        line = NULL;
    }
    if (fclose(file) && line) {
        error = errno;
        free(line);
        line = NULL;
    }
    if (!line) errno = error;
    return line;
}

static int unlock_exact_name(const char *name)
{
    int fd = open("/sys/power/wake_unlock", O_WRONLY | O_CLOEXEC);
    if (fd < 0) return -1;
    size_t length = strlen(name);
    ssize_t count;
    do {
        count = write(fd, name, length);
    } while (count < 0 && errno == EINTR);
    int error = count < 0 ? errno : EIO;
    int close_result = close(fd);
    if (count != (ssize_t)length) { errno = error; return -1; }
    return close_result;
}

/* 仅释放本轮新建的同名锁，历史遗留锁保持原状 */
static int release_owned_lock(pid_t child, const char *before)
{
    char name[48];
    snprintf(name, sizeof(name), "sscrpcd:%u", (unsigned)child);
    int preexisting = count_lock_name(before, name) != 0;
    int active = -1, remaining = -1, wrote = 0, error = 0;
    char *current = read_active_locks();
    if (!current) {
        error = errno;
    } else {
        active = count_lock_name(current, name);
        free(current);
        remaining = active;
        if (active && preexisting) {
            error = EEXIST;
        } else if (active > 1) {
            error = EIO;
        } else if (active == 1) {
            if (unlock_exact_name(name)) {
                error = errno;
            } else {
                wrote = 1;
                current = read_active_locks();
                if (!current) {
                    remaining = -1;
                    error = errno;
                } else {
                    remaining = count_lock_name(current, name);
                    free(current);
                    if (remaining) error = EBUSY;
                }
            }
        }
    }
    printf("SENSORSPD_WAKE_CLEANUP pid=%u preexisting=%d active=%d wrote=%d remaining=%d errno=%d\n",
        (unsigned)child, preexisting, active, wrote, remaining, error);
    return error ? 74 : 0;
}

static int finish_owned_child(pid_t child, int *status, const char *before)
{
    /* 子进程已退出且尚未回收，锁名中的 PID 不会被复用 */
    int cleanup = release_owned_lock(child, before);
    pid_t result;
    do {
        result = waitpid(child, status, 0);
    } while (result < 0 && errno == EINTR);
    if (result != child) return failed("reap");
    return cleanup;
}

static int prepare_identity(const char *root)
{
    if (chdir(root) || chroot(".") || chdir("/")) return failed("chroot");
    /* 增加system堆所属组，保留原wakelock组及阻止休眠能力 */
    gid_t groups[] = {1000, 3010, 3070};
    if (setgroups(3, groups) || setresgid(1000, 1000, 1000) ||
        prctl(PR_SET_KEEPCAPS, 1L) || setresuid(1000, 1000, 1000)) return failed("credentials");
    struct __user_cap_header_struct header = {_LINUX_CAPABILITY_VERSION_3, 0};
    struct __user_cap_data_struct data[2] = {{0}};
    data[CAP_BLOCK_SUSPEND / 32].effective = 1U << (CAP_BLOCK_SUSPEND % 32);
    data[CAP_BLOCK_SUSPEND / 32].permitted = data[CAP_BLOCK_SUSPEND / 32].effective;
    data[CAP_BLOCK_SUSPEND / 32].inheritable = data[CAP_BLOCK_SUSPEND / 32].effective;
    if (syscall(SYS_capset, &header, data) ||
        prctl(PR_CAP_AMBIENT, PR_CAP_AMBIENT_RAISE, CAP_BLOCK_SUSPEND, 0L, 0L) ||
        prctl(PR_SET_KEEPCAPS, 0L)) return failed("capabilities");
    /* 原进程只保留阻止休眠能力，监督器在外层回收资源 */
    return 0;
}

static int execute_original(void)
{
    if (clearenv() || setenv("LD_LIBRARY_PATH", "/vendor/lib64:/system/lib64", 1) ||
        setenv("LD_PRELOAD", "/vendor/lib64/libsensor_log_stderr.so", 1) ||
        setenv("PATH", "/system/bin:/vendor/bin", 1)) return failed("environment");
    printf("SENSORSPD_EXEC uid=%u gid=%u pid=%u argument=sensorspd\n",
        (unsigned)getuid(), (unsigned)getgid(), (unsigned)getpid());
    fflush(stdout);
    int quiet = open("/dev/null", O_RDWR | O_CLOEXEC);
    if (quiet < 0 || dup2(quiet, STDOUT_FILENO) < 0 || dup2(quiet, STDERR_FILENO) < 0)
        return failed("stdio");
    if (quiet > STDERR_FILENO) close(quiet);
    char *const args[] = {"/system/bin/linker64", "/vendor/bin/sscrpcd", "sensorspd", NULL};
    execv(args[0], args);
    return failed("exec");
}

struct wake_node {
    const char *source;
    char target[PATH_MAX];
    struct stat original;
    int changed;
    int bound;
};

static int prepare_wake_nodes(const char *root, struct wake_node nodes[2])
{
    nodes[0].source = "/sys/power/wake_lock";
    nodes[1].source = "/sys/power/wake_unlock";
    for (unsigned i = 0; i < 2; ++i) {
        if (stat(nodes[i].source, &nodes[i].original)) return failed("wake_stat");
        int length = snprintf(nodes[i].target, sizeof(nodes[i].target), "%s%s", root, nodes[i].source);
        if (length < 0 || (size_t)length >= sizeof(nodes[i].target)) { errno = ENAMETOOLONG; return failed("wake_path"); }
    }
    for (unsigned i = 0; i < 2; ++i) {
        nodes[i].changed = 1;
        if (chown(nodes[i].source, (uid_t)-1, 3010) || chmod(nodes[i].source, 0664)) return failed("wake_permissions");
        if (mount(nodes[i].source, nodes[i].target, NULL, MS_BIND, NULL)) return failed("wake_bind");
        nodes[i].bound = 1;
        if (mount(NULL, nodes[i].target, NULL, MS_BIND | MS_REMOUNT, NULL)) return failed("wake_rw");
    }
    return 0;
}

/* 子进程退出后恢复原权限，私有挂载不影响其它命名空间 */
static int restore_wake_nodes(struct wake_node nodes[2])
{
    int result = 0;
    for (unsigned i = 0; i < 2; ++i) {
        if (!nodes[i].changed) continue;
        int owner = chown(nodes[i].source, nodes[i].original.st_uid, nodes[i].original.st_gid);
        int owner_error = owner ? errno : 0;
        int mode = chmod(nodes[i].source, nodes[i].original.st_mode & 07777);
        int mode_error = mode ? errno : 0;
        printf("SENSORSPD_WAKE_RESTORE node=%u owner_rc=%d owner_errno=%d mode_rc=%d mode_errno=%d\n",
            i, owner, owner_error, mode, mode_error);
        if (owner || mode) result = 74;
    }
    for (int i = 1; i >= 0; --i) {
        if (nodes[i].bound && umount(nodes[i].target)) {
            printf("SENSORSPD_WAKE_UNMOUNT node=%d errno=%d\n", i, errno);
            result = 74;
        }
    }
    return result;
}

int main(int argc, char **argv)
{
    if (argc != 2 || argv[1][0] != '/') return 64;
    setvbuf(stdout, NULL, _IOLBF, 0);
    if (geteuid() != 0) { errno = EPERM; return failed("supervisor_uid"); }
    /* FD9由启动脚本持有，原进程不继承此启动锁 */
    if (flock(9, LOCK_EX | LOCK_NB) || fcntl(9, F_SETFD, FD_CLOEXEC)) return failed("startup_lock");
    struct sigaction action = {0};
    sigemptyset(&action.sa_mask);
    action.sa_handler = requested_stop;
    if (sigaction(SIGTERM, &action, NULL) || sigaction(SIGINT, &action, NULL) ||
        sigaction(SIGHUP, &action, NULL)) return failed("signals");
    action.sa_handler = child_changed;
    if (sigaction(SIGCHLD, &action, NULL)) return failed("child_signal");
    if (getsid(0) != getpid() && setsid() < 0) return failed("supervisor_session");

    struct wake_node nodes[2] = {0};
    int result = prepare_wake_nodes(argv[1], nodes);
    char *before = NULL;
    if (!result) {
        before = read_active_locks();
        if (!before) result = failed("wake_snapshot");
    }
    if (result || stop_requested) {
        free(before);
        int restored = restore_wake_nodes(nodes);
        if (restored) result = restored;
        printf("SENSORSPD_SUPERVISOR_DONE result=%d stopped_by_signal=%d\n", result, (int)stop_requested);
        close(9);
        return result;
    }

    pid_t own_parent = getpid();
    pid_t child = fork();
    if (child < 0) {
        result = failed("fork");
    } else if (!child) {
        free(before);
        close(9);
        action.sa_handler = SIG_DFL;
        sigaction(SIGTERM, &action, NULL); sigaction(SIGINT, &action, NULL); sigaction(SIGHUP, &action, NULL);
        if (stop_requested) _exit(128 + stop_requested);
        if (prepare_identity(argv[1])) _exit(70);
        /* 身份切换后设置，监督器消失时不遗留原进程 */
        if (prctl(PR_SET_PDEATHSIG, SIGKILL) || getppid() != own_parent) _exit(72);
        _exit(execute_original());
    } else {
        printf("SENSORSPD_CHILD pid=%u lifetime=continuous\n", (unsigned)child);
        int exited = 0;
        sigset_t blocked, previous, waiting;
        sigemptyset(&blocked);
        sigaddset(&blocked, SIGTERM); sigaddset(&blocked, SIGINT);
        sigaddset(&blocked, SIGHUP); sigaddset(&blocked, SIGCHLD);
        int mask_active = sigprocmask(SIG_BLOCK, &blocked, &previous) == 0;
        if (!mask_active) result = failed("signal_mask");
        else {
            waiting = previous;
            sigdelset(&waiting, SIGTERM); sigdelset(&waiting, SIGINT);
            sigdelset(&waiting, SIGHUP); sigdelset(&waiting, SIGCHLD);
        }
        /* 检查状态与原子解锁等待之间不丢失TERM或子进程退出 */
        while (!stop_requested && !result) {
            int observed = child_status(child);
            if (observed == 1) { exited = 1; break; }
            if (observed < 0) { result = failed("wait_child"); break; }
            sigsuspend(&waiting);
        }
        if (mask_active && sigprocmask(SIG_SETMASK, &previous, NULL)) result = failed("signal_restore");
        if (!exited) {
            printf("SENSORSPD_SUPERVISOR_STOP_REQUEST stopped_by_signal=%d\n", (int)stop_requested);
            if (kill(child, SIGTERM) && errno != ESRCH) result = failed("term");
            int waited = wait_owned_child(child, 1000);
            if (!waited) {
                if (kill(child, SIGKILL) && errno != ESRCH) result = failed("kill");
                waited = wait_owned_child(child, 1000);
            }
            if (waited == 1) exited = 1;
            else {
                printf("SENSORSPD_CLEANUP_HOLD child=%u result=%d\n", (unsigned)child, waited);
                result = 90;
            }
        }
        if (exited) {
            int status = 0;
            int cleanup = finish_owned_child(child, &status, before);
            printf("SENSORSPD_CHILD_DONE cleanup=%d exit=%d signal=%d stopped_by_signal=%d\n", cleanup,
                WIFEXITED(status) ? WEXITSTATUS(status) : -1, WIFSIGNALED(status) ? WTERMSIG(status) : 0,
                (int)stop_requested);
            if (cleanup) result = cleanup;
            else if (!stop_requested && !result) {
                result = WIFEXITED(status) && WEXITSTATUS(status) ? WEXITSTATUS(status) : 4;
            }
        }
    }
    free(before);
    int restored = restore_wake_nodes(nodes);
    if (restored) result = restored;
    printf("SENSORSPD_SUPERVISOR_DONE result=%d stopped_by_signal=%d\n", result, (int)stop_requested);
    close(9);
    return result;
}

