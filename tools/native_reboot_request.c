/* Explicit maintenance reboot; run only after logs and recovery images are saved. */
#define _GNU_SOURCE
#include <linux/reboot.h>
#include <stdio.h>
#include <string.h>
#include <sys/syscall.h>
#include <unistd.h>

int main(int argc, char **argv)
{
    if (argc != 2 || (strcmp(argv[1], "bootloader") && strcmp(argv[1], "recovery"))) return 2;
    printf("MAINTENANCE_REBOOT=%s\n", argv[1]); fflush(stdout);
    sync();
    syscall(SYS_reboot, LINUX_REBOOT_MAGIC1, LINUX_REBOOT_MAGIC2, LINUX_REBOOT_CMD_RESTART2, argv[1]);
    perror("reboot");
    return 3;
}
