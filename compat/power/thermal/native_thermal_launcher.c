#include <stdio.h>
#include <stdlib.h>
#include <unistd.h>


int main(int argc, char **argv)
{
    if (argc != 2) {
        fprintf(stderr, "usage: native_thermal_launcher ROOT\n");
        return 2;
    }

    // 隔离原厂配置路径，沿用已有安卓运行库
    if (chroot(argv[1]) != 0 || chdir("/") != 0) {
        perror("thermal chroot");
        return 1;
    }
    if (setenv("LD_LIBRARY_PATH", "/compat/audio-runtime/lib64", 1) != 0) {
        perror("thermal library path");
        return 1;
    }

    // 保持前台进程，交由系统初始化服务管理生命周期
    execl("/compat/audio-runtime/bin/linker64", "linker64",
        "/bin/mi_thermald", (char *)NULL);
    perror("thermal exec");
    return 1;
}
