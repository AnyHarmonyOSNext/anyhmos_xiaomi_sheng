/* Read-only stock xiaomi_touch.ko raw transport probe. No controller commands. */
#include <errno.h>
#include <fcntl.h>
#include <poll.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/ioctl.h>
#include <sys/mman.h>
#include <time.h>
#include <unistd.h>

static double now(void) {
    struct timespec t; clock_gettime(CLOCK_MONOTONIC, &t);
    return t.tv_sec + t.tv_nsec / 1e9;
}
static uint32_t hash(const unsigned char *p, size_t n) {
    uint32_t h=2166136261U;
    for(size_t i=0;i<n;i++) h=(h^p[i])*16777619U;
    return h;
}
int main(int argc, char **argv) {
    const char *path=argc>1?argv[1]:"/dev/xiaomi-touch";
    int seconds=argc>2?atoi(argv[2]):8;
    if(seconds<1 || seconds>60) return 2;
    setvbuf(stdout,NULL,_IOLBF,0);
    int fd=open(path,O_RDONLY|O_NONBLOCK|O_CLOEXEC);
    if(fd<0){perror("open");return 3;}
    if(ioctl(fd,_IO('T',3),0UL)<0){perror("select panel");return 4;}
    unsigned char param[214]={0};
    if(ioctl(fd,_IOR('T',1,unsigned char[214]),param)<0){perror("parameters");return 5;}
    printf("PARAM214=");for(size_t i=0;i<sizeof(param);i++)printf("%02x",param[i]);puts("");
    size_t stride=(size_t)param[9]*4096, count=param[10], length=stride*count;
    printf("RAW_LAYOUT stride=%zu count=%zu length=%zu\n",stride,count,length);
    if(stride<5160 || stride>65536 || count<2 || count>64 || length>1048576) return 6;
    if(ioctl(fd,_IO('T',2),1UL)<0){perror("select raw mmap");return 7;}
    const unsigned char *map=mmap(NULL,length,PROT_READ,MAP_SHARED,fd,0);
    if(map==MAP_FAILED){perror("mmap");return 8;}
    printf("RAW_MAPPED first_hash=%08x head=",hash(map,5160));
    for(int i=0;i<96;i++)printf("%02x",map[i]);puts("");
    double end=now()+seconds; unsigned frames=0, changed=0, polls=0; uint32_t prev=0;
    while(now()<end) {
        struct pollfd p={fd,POLLIN|POLLRDNORM,0};
        int ready=poll(&p,1,100); if(ready<0 && errno!=EINTR){perror("poll");break;}
        if(ready>0)polls++;
        errno=0; int index=ioctl(fd,_IO('T',4),0UL);
        if(index<0){usleep(10000);continue;}
        if((size_t)index>=count){printf("BAD_INDEX=%d\n",index);return 9;}
        unsigned char frame[5160];memcpy(frame,map+(size_t)index*stride,sizeof(frame));
        uint32_t h=hash(frame,sizeof(frame));if(frames && h!=prev)changed++;prev=h;
        if(frames<4 || frames%120==0)printf("RAW_FRAME n=%u index=%d hash=%08x poll=%x\n",frames,index,h,p.revents);
        if(frames==0 && argc>3) {
            int out=open(argv[3],O_WRONLY|O_CREAT|O_EXCL|O_CLOEXEC,0600);
            if(out<0){perror("sample create");return 10;}
            if(write(out,frame,sizeof(frame))!=(ssize_t)sizeof(frame)){perror("sample write");return 11;}
            close(out);
        }
        frames++;
    }
    printf("RAW_RESULT frames=%u changed=%u poll_ready=%u\n",frames,changed,polls);
    munmap((void*)map,length);close(fd);return frames?0:12;
}
