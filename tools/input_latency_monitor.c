/* SPDX-License-Identifier: MIT - read-only evdev latency observation; no grab. */
#define _GNU_SOURCE
#include <linux/input.h>
#include <sys/ioctl.h>
#include <time.h>
#include <fcntl.h>
#include <poll.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <unistd.h>
#include <errno.h>
#include <string.h>
static int64_t mono_us(void){struct timespec t;clock_gettime(CLOCK_MONOTONIC,&t);return (int64_t)t.tv_sec*1000000+t.tv_nsec/1000;}
int main(int argc,char **argv)
{
    if(argc<3) return 1;
    int secs=atoi(argv[1]);if(secs<1||secs>90||argc>7)return 1;
    struct pollfd p[5];int have[5]={0},active[5]={0};int64_t last[5]={0};
    setbuf(stdout,0);int clockid=CLOCK_MONOTONIC;
    for(int i=2;i<argc;i++){
        p[i-2]=(struct pollfd){.fd=open(argv[i],O_RDONLY|O_NONBLOCK|O_CLOEXEC),.events=POLLIN};
        if(p[i-2].fd<0){perror(argv[i]);return 2;}
        if(ioctl(p[i-2].fd,EVIOCSCLOCKID,&clockid)){perror("event monotonic clock");return 3;}
        printf("INPUT_MONITOR node=%s clock=monotonic no_grab=1\n",argv[i]);
    }
    int64_t end=mono_us()+(int64_t)secs*1000000;
    while(mono_us()<end){
        int rc=poll(p,argc-2,100);if(rc<0&&errno!=EINTR)return 4;
        for(int j=0;j<argc-2;j++)if(p[j].revents&POLLIN){
            struct input_event events[128];ssize_t n;
            while((n=read(p[j].fd,events,sizeof(events)))>0){
                int64_t now=mono_us();
                for(unsigned k=0;k<(unsigned)n/sizeof(events[0]);k++){
                    struct input_event *e=&events[k];
                    int64_t ts=(int64_t)e->time.tv_sec*1000000+e->time.tv_usec;
                    if(e->type==EV_ABS||e->type==EV_KEY){have[j]=1;}
                    if(e->type==EV_KEY && e->code==BTN_TOUCH){active[j]=e->value;printf("TOUCH node=%s down=%d event_us=%lld recv_us=%lld queue_us=%lld\n",argv[j+2],e->value,(long long)ts,(long long)now,(long long)(now-ts));}
                    if(e->type==EV_SYN&&e->code==SYN_REPORT&&have[j]){
                        printf("FRAME node=%s event_us=%lld recv_us=%lld queue_us=%lld gap_us=%lld active=%d\n",argv[j+2],(long long)ts,(long long)now,(long long)(now-ts),(long long)(last[j]?ts-last[j]:0),active[j]);
                        last[j]=ts;have[j]=0;
                    }
                }
            }
        }
    }
    for(int j=0;j<argc-2;j++)close(p[j].fd);
    printf("INPUT_MONITOR_EXIT=0\n");return 0;
}
