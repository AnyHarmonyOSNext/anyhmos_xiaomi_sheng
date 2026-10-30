#define _GNU_SOURCE
#include <stdio.h>
#include <time.h>
int main(void){int ids[]={CLOCK_REALTIME,CLOCK_MONOTONIC,CLOCK_MONOTONIC_RAW,CLOCK_BOOTTIME};const char*names[]={"REALTIME","MONOTONIC","MONOTONIC_RAW","BOOTTIME"};for(unsigned i=0;i<4;i++){struct timespec t;if(clock_gettime(ids[i],&t))return 1;printf("CLOCK_%s=%lld.%09ld\n",names[i],(long long)t.tv_sec,t.tv_nsec);}return 0;}
