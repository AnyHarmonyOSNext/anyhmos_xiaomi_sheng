/* SPDX-License-Identifier: MIT - original snapshot CLI under ordinary shell UID.
 * No token/permission checks are patched; this matches its supported shell path.
 */
#define _GNU_SOURCE
#include <unistd.h>
#include <grp.h>
#include <stdio.h>
int main(void){
    setbuf(stdout,NULL);
    if(geteuid()!=0){puts("SNAPSHOT_SHELL_FAIL root launcher required");return 1;}
    if(setgroups(0,NULL)||setgid(2000)||setuid(2000)){perror("drop to shell");return 1;}
    printf("SNAPSHOT_SHELL uid=%u euid=%u gid=%u\n",getuid(),geteuid(),getgid());
    char *args[]={"/system/bin/snapshot_display","-i","0","-f","/data/local/tmp/shell-capture/display0.jpeg",NULL};
    execv(args[0],args);perror("exec original snapshot_display");return 1;
}
