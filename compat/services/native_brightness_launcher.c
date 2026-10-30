/* Keep the donor init identity and make early startup failures observable. */
#include <fcntl.h>
#include <stdio.h>
#include <unistd.h>
int main(void)
{
    int fd = open("/data/local/tmp/sheng-brightness-stderr.txt",
        O_WRONLY | O_APPEND | O_CLOEXEC | O_NOFOLLOW);
    if (fd < 0) return 2;
    if (dup2(fd, 1) < 0 || dup2(fd, 2) < 0) return 3;
    close(fd);
    dprintf(2, "BRIGHTNESS_NATIVE_LAUNCH uid=%d gid=%d\n", getuid(), getgid());
    /* sa_main derives the registered process name from this basename. */
    execl("/system/bin/sa_main", "sa_main", "/compat/etc/powermgr.json", (char *)0);
    perror("brightness sa_main exec");
    return 4;
}
