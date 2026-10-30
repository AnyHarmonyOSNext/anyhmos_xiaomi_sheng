/* SPDX-License-Identifier: MIT
 * Bounded read-only radio logging. O_DSYNC preserves the last available record.
 */
#define _GNU_SOURCE
#include <errno.h>
#include <fcntl.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <time.h>
#include <unistd.h>

static void append(int out, const char *prefix, const char *data, size_t size)
{
    if (write(out, prefix, strlen(prefix)) < 0) return;
    while (size) {
        ssize_t n = write(out, data, size);
        if (n < 0 && errno == EINTR) continue;
        if (n <= 0) break;
        data += n;
        size -= (size_t)n;
    }
}

int main(int argc, char **argv)
{
    if (argc != 3) return 2;
    int seconds = atoi(argv[2]);
    if (seconds < 1 || seconds > 120) return 2;
    int out = open(argv[1], O_WRONLY | O_CREAT | O_EXCL | O_DSYNC | O_CLOEXEC, 0600);
    int kmsg = open("/dev/kmsg", O_RDONLY | O_NONBLOCK | O_CLOEXEC);
    if (out < 0 || kmsg < 0) return 3;
    (void)lseek(kmsg, 0, SEEK_END);
    char buffer[16385];
    struct timespec now;
    clock_gettime(CLOCK_MONOTONIC, &now);
    time_t end = now.tv_sec + seconds;
    append(out, "CAPTURE_BEGIN\n", "", 0);
    for (;;) {
        clock_gettime(CLOCK_MONOTONIC, &now);
        if (now.tv_sec >= end) break;
        for (int i = 0; i < 128; ++i) {
            ssize_t n = read(kmsg, buffer, sizeof(buffer) - 1);
            if (n < 0 && errno == EPIPE) continue;
            if (n <= 0) break;
            buffer[n] = 0;
            if (strcasestr(buffer, "cnss") || strcasestr(buffer, "mhi") ||
                strcasestr(buffer, "firmware") || strcasestr(buffer, "panic") ||
                strcasestr(buffer, "BUG:") || strcasestr(buffer, "Call trace") ||
                strcasestr(buffer, "CFI") || strcasestr(buffer, "watchdog") ||
                strcasestr(buffer, " pc :") || strcasestr(buffer, " lr :"))
                append(out, "KMSG ", buffer, (size_t)n);
        }
        usleep(10000);
    }
    append(out, "CAPTURE_END\n", "", 0);
    close(kmsg);
    close(out);
    return 0;
}
