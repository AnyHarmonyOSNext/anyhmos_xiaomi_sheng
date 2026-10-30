/* SPDX-License-Identifier: MIT
 * Interaction floor for the stock GPU governor. Never change maximum/thermal.
 */
#define _GNU_SOURCE
#include <drm.h>
#include <drm_mode.h>
#include <errno.h>
#include <fcntl.h>
#include <linux/input.h>
#include <poll.h>
#include <signal.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/file.h>
#include <sys/ioctl.h>
#include <time.h>
#include <unistd.h>

static volatile sig_atomic_t running=1;
static const char*minimum="/sys/class/kgsl/kgsl-3d0/devfreq/min_freq";
static uint64_t now(void){struct timespec t;clock_gettime(CLOCK_MONOTONIC,&t);return (uint64_t)t.tv_sec*1000000000+t.tv_nsec;}
static void stop(int sig){(void)sig;running=0;}
static unsigned long read_frequency(const char*path){unsigned long value=0;FILE*f=fopen(path,"r");if(f){if(fscanf(f,"%lu",&value)!=1)value=0;fclose(f);}return value;}
static int set_frequency(unsigned long value){
 int fd=open(minimum,O_WRONLY|O_CLOEXEC);if(fd<0)return -1;char text[32];int n=snprintf(text,sizeof(text),"%lu\n",value);ssize_t rc;
 do{rc=write(fd,text,n);}while(rc<0&&errno==EINTR);int saved=errno;close(fd);errno=saved;
 if(rc!=n||read_frequency(minimum)!=value)return -1;return 0;
}
static int touch_node(void){
 for(unsigned i=0;i<32;i++){char path[64],name[128]={0};snprintf(path,sizeof(path),"/dev/input/event%u",i);int fd=open(path,O_RDONLY|O_CLOEXEC|O_NONBLOCK);if(fd<0)continue;
  if(ioctl(fd,EVIOCGNAME(sizeof(name)),name)>=0&&!strcmp(name,"Sheng THP Compat Touchscreen"))return fd;close(fd);
 }return -1;
}
int main(void){
 if(!freopen("/data/local/tmp/sheng-gpu-policy.txt","a",stdout))return 1;
 setbuf(stdout,NULL);signal(SIGTERM,stop);signal(SIGINT,stop);
 int lock=open("/data/local/tmp/sheng-gpu-policy.lock",O_CREAT|O_RDWR|O_CLOEXEC,0600);if(lock<0||flock(lock,LOCK_EX|LOCK_NB))return 2;
 unsigned long saved=read_frequency(minimum),max=read_frequency("/sys/class/kgsl/kgsl-3d0/devfreq/max_freq");
 if(!saved||!max)return 3;unsigned long floor=max<550000000UL?max:550000000UL;if(floor<saved)floor=saved;
 int card=open("/dev/dri/card0",O_RDWR|O_CLOEXEC),input=-1,touching=0,boosted=0;uint32_t plane=0,previous=0;
 if(card<0)return 4;
 /* The first primary-node open can implicitly become master. This observer
  * must release its own ownership before the unprivileged composer starts.
  * DROP_MASTER on a non-master fd cannot affect another client's master.
  */
 if(ioctl(card,DRM_IOCTL_DROP_MASTER,0)&&errno!=EACCES&&errno!=EINVAL){perror("drop observer master");close(card);return 7;}
 struct drm_set_client_cap cap={.capability=DRM_CLIENT_CAP_UNIVERSAL_PLANES,.value=1};if(ioctl(card,DRM_IOCTL_SET_CLIENT_CAP,&cap))return 5;
 uint64_t until=0,retry=0;printf("GPU_POLICY_READY saved=%lu interactive=%lu maximum_unchanged=%lu hold_ms=500\n",saved,floor,max);
 while(running){
  uint64_t t=now();if(input<0&&t>=retry){input=touch_node();retry=t+1000000000ULL;}
  struct pollfd p={.fd=input,.events=POLLIN};int rc=poll(&p,1,8);
  if(rc>0&&(p.revents&POLLIN)){struct input_event events[128];ssize_t bytes=read(input,events,sizeof(events));
   if(bytes>0)for(size_t i=0;i<(size_t)bytes/sizeof(events[0]);i++)if(events[i].type==EV_KEY&&events[i].code==BTN_TOUCH)touching=!!events[i].value;
  }
  if(rc>0&&(p.revents&(POLLERR|POLLHUP|POLLNVAL))){close(input);input=-1;touching=0;}
  if(!plane){uint32_t ids[64];struct drm_mode_get_plane_res r={.plane_id_ptr=(uintptr_t)ids,.count_planes=64};
   if(!ioctl(card,DRM_IOCTL_MODE_GETPLANERESOURCES,&r)&&r.count_planes<=64)for(unsigned i=0;i<r.count_planes;i++){
    struct drm_mode_get_plane q={.plane_id=ids[i]};if(!ioctl(card,DRM_IOCTL_MODE_GETPLANE,&q)&&q.crtc_id&&q.fb_id){plane=ids[i];break;}
   }
  }
  int active=0;struct drm_mode_get_plane q={.plane_id=plane};
  if(plane&&!ioctl(card,DRM_IOCTL_MODE_GETPLANE,&q)&&q.crtc_id&&q.fb_id){active=1;if(q.fb_id!=previous){previous=q.fb_id;until=t+500000000ULL;}}
  if(touching&&active)until=t+500000000ULL;
  int wanted=active&&t<until&&access("/data/local/tmp/sheng-gpu-policy-disabled",F_OK)!=0;
  if(wanted!=boosted){unsigned long target=wanted?floor:saved;if(set_frequency(target)){printf("GPU_POLICY_WRITE_FAILED target=%lu errno=%d\n",target,errno);break;}
   boosted=wanted;printf("GPU_POLICY_APPLIED t_ns=%llu min=%lu active=%d touch=%d\n",(unsigned long long)t,target,active,touching);
  }
 }
 int rc=set_frequency(saved);printf("GPU_POLICY_EXIT restored=%lu verified=%d\n",saved,rc==0);if(input>=0)close(input);close(card);close(lock);return rc?6:0;
}
