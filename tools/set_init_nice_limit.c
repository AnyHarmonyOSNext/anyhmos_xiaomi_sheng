/* SPDX-License-Identifier: MIT
 * Restore only the original donor init RLIMIT_NICE=40:40 in this RAM trial.
 * PID 1 and the expected old/current value are explicitly checked/logged.
 */
#define _GNU_SOURCE
#include <stdio.h>
#include <sys/resource.h>
#include <sys/syscall.h>
#include <unistd.h>
#include <errno.h>
#include <string.h>
int main(void){
    struct rlimit before,after,wanted={40,40};
    if(geteuid()!=0){puts("NICE_LIMIT_FAIL root required");return 1;}
    if(syscall(SYS_prlimit64,1,RLIMIT_NICE,NULL,&before)){perror("prlimit read PID1");return 1;}
    printf("PID1_NICE_BEFORE soft=%llu hard=%llu\n",(unsigned long long)before.rlim_cur,(unsigned long long)before.rlim_max);
    if(before.rlim_cur!=0&&before.rlim_cur!=40){puts("NICE_LIMIT_FAIL unexpected soft");return 1;}
    if(before.rlim_max!=0&&before.rlim_max!=40){puts("NICE_LIMIT_FAIL unexpected hard");return 1;}
    if(syscall(SYS_prlimit64,1,RLIMIT_NICE,&wanted,NULL)){perror("prlimit write PID1");return 1;}
    if(syscall(SYS_prlimit64,1,RLIMIT_NICE,NULL,&after)){perror("prlimit verify");return 1;}
    printf("PID1_NICE_AFTER soft=%llu hard=%llu\n",(unsigned long long)after.rlim_cur,(unsigned long long)after.rlim_max);
    return after.rlim_cur!=40||after.rlim_max!=40;
}
