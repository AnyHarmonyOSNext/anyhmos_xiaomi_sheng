#include <unistd.h>
#include <stdlib.h>
#include <stdio.h>
#include <fcntl.h>
int main(void) {
 int fd=open("/data/local/tmp/sheng-graphics/bootanimation-adapter.log",O_WRONLY|O_APPEND);
 if(fd>=0){dup2(fd,1);dup2(fd,2);if(fd>2)close(fd);}
 fprintf(stderr,"SHENG_LAUNCH uid=%d euid=%d pid=%d\n",getuid(),geteuid(),getpid());
 if(setenv("LD_PRELOAD","/data/local/tmp/sheng-graphics/libsheng_boot_vulkan.so",1)){perror("setenv");return 1;}
 execl("/data/local/tmp/sheng-graphics/bootanimation-real","bootanimation",(char*)0);
 perror("exec bootanimation-real");return 2;
}
