/* Run an original diagnostic CLI with its supported ordinary shell identity. */
#define _GNU_SOURCE
#include <unistd.h>
#include <grp.h>
#include <stdio.h>
#include <string.h>
int main(int argc,char **argv){
    if(argc<2 || strncmp(argv[1],"/system/bin/",12))return 2;
    if(geteuid()!=0 || setgroups(0,NULL) || setgid(2000) || setuid(2000))return 3;
    printf("ORIGINAL_SHELL_CLI uid=%u gid=%u\n",getuid(),getgid());fflush(stdout);
    execv(argv[1],argv+1);perror("exec original CLI");return 4;
}
