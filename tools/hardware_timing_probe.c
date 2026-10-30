/* SPDX-License-Identifier: MIT
 * Bounded, read-only vblank/evdev timing. No master, modeset, or EVIOCGRAB.
 */
#define _GNU_SOURCE
#include <drm/drm.h>
#include <drm/drm_mode.h>
#include <errno.h>
#include <fcntl.h>
#include <linux/input.h>
#include <poll.h>
#include <pthread.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/ioctl.h>
#include <time.h>
#include <unistd.h>

static int card, crtc_index;
static uint64_t deadline;
static uint64_t ns(void) {struct timespec t;clock_gettime(CLOCK_MONOTONIC,&t);return (uint64_t)t.tv_sec*1000000000+t.tv_nsec;}
struct stats {uint64_t previous,count,sum,max,bins[9];};
static void add(struct stats*s,uint64_t value) {
 const uint64_t limits[]={2000000,4000000,6000000,8000000,12000000,17000000,25000000,100000000};
 unsigned i=0;while(i<8&&value>limits[i])i++;s->bins[i]++;s->count++;s->sum+=value;if(value>s->max)s->max=value;
}
static void gap(struct stats*s,uint64_t t) {if(s->previous&&t>s->previous)add(s,t-s->previous);s->previous=t;}
static void printstats(const char*name,const struct stats*s) {
 printf("%s count=%llu mean_ms=%.3f max_ms=%.3f bins_le_ms=2,4,6,8,12,17,25,100,inf counts=",name,
 (unsigned long long)s->count,s->count?(double)s->sum/s->count/1e6:0,s->max/1e6);
 for(unsigned i=0;i<9;i++)printf("%s%llu",i?",":"",(unsigned long long)s->bins[i]);puts("");
}
static void properties(uint32_t object,uint32_t type) {
 uint32_t ids[256];uint64_t values[256];struct drm_mode_obj_get_properties p={.props_ptr=(uintptr_t)ids,.prop_values_ptr=(uintptr_t)values,.count_props=256,.obj_id=object,.obj_type=type};
 if(ioctl(card,DRM_IOCTL_MODE_OBJ_GETPROPERTIES,&p)||p.count_props>256)return;
 for(unsigned i=0;i<p.count_props;i++){
  struct drm_mode_get_property prop={.prop_id=ids[i]};if(ioctl(card,DRM_IOCTL_MODE_GETPROPERTY,&prop))continue;
  if(strstr(prop.name,"fence")||strstr(prop.name,"FENCE")||strstr(prop.name,"sync")||!strcmp(prop.name,"ACTIVE"))
   printf("PROPERTY object=%u id=%u name=%s value=%llu flags=0x%x\n",object,ids[i],prop.name,(unsigned long long)values[i],prop.flags);
 }
}
static void*vblank(void*unused) {
 (void)unused;struct stats stamps={0},wall={0};unsigned errors=0;uint32_t first=0,last=0;
 while(ns()<deadline) {
  union drm_wait_vblank v={.request={.type=_DRM_VBLANK_RELATIVE|(crtc_index<<_DRM_VBLANK_HIGH_CRTC_SHIFT),.sequence=1}};
  if(ioctl(card,DRM_IOCTL_WAIT_VBLANK,&v)){errors++;break;}
  uint64_t t=(uint64_t)v.reply.tval_sec*1000000000+(uint64_t)v.reply.tval_usec*1000;
  gap(&stamps,t);gap(&wall,ns());if(!first)first=v.reply.sequence;last=v.reply.sequence;
 }
 printf("VBLANK_SEQUENCE first=%u last=%u errors=%u\n",first,last,errors);printstats("VBLANK_TIMESTAMP_GAP",&stamps);printstats("VBLANK_WALL_GAP",&wall);return NULL;
}
int main(int argc,char**argv) {
 unsigned seconds=argc>1?(unsigned)atoi(argv[1]):20;if(seconds<1||seconds>40)return 2;alarm(seconds+5);setbuf(stdout,NULL);
 card=open("/dev/dri/card0",O_RDWR|O_CLOEXEC);if(card<0){perror("card0");return 3;}
 struct drm_set_client_cap cap={.capability=DRM_CLIENT_CAP_ATOMIC,.value=1};if(ioctl(card,DRM_IOCTL_SET_CLIENT_CAP,&cap)){perror("atomic cap");return 4;}
 uint32_t crtcs[32];struct drm_mode_card_res res={.crtc_id_ptr=(uintptr_t)crtcs,.count_crtcs=32};if(ioctl(card,DRM_IOCTL_MODE_GETRESOURCES,&res)||res.count_crtcs>32)return 5;
 uint32_t active=0;for(unsigned i=0;i<res.count_crtcs;i++){
  struct drm_mode_crtc c={.crtc_id=crtcs[i]};if(ioctl(card,DRM_IOCTL_MODE_GETCRTC,&c)||!c.mode_valid||c.mode.hdisplay!=3048||c.mode.vdisplay!=2032)continue;
  active=c.crtc_id;crtc_index=i;printf("MODE id=%u name=%s nominal_hz=%u clock=%u totals=%ux%u\n",active,c.mode.name,c.mode.vrefresh,c.mode.clock,c.mode.htotal,c.mode.vtotal);break;
 }
 if(!active)return 6;properties(active,DRM_MODE_OBJECT_CRTC);
 int input=-1;for(unsigned i=0;i<32;i++){
  char path[80],name[128]={0};snprintf(path,sizeof(path),"/dev/input/event%u",i);int fd=open(path,O_RDONLY|O_CLOEXEC|O_NONBLOCK);if(fd<0)continue;
  if(ioctl(fd,EVIOCGNAME(sizeof(name)),name)>=0&&!strcmp(name,"Sheng THP Compat Touchscreen")){input=fd;printf("TOUCH_NODE path=%s name=%s\n",path,name);break;}close(fd);
 }
 if(input<0){puts("TOUCH_NODE_MISSING");return 7;}int clock=CLOCK_MONOTONIC;if(ioctl(input,EVIOCSCLOCKID,&clock)){perror("input monotonic");return 8;}
 struct stats touch={0},age={0};unsigned touchframes=0,dropped=0,frames=0;int touching=0,was=0;
 deadline=ns()+(uint64_t)seconds*1000000000;pthread_t thread;if(pthread_create(&thread,NULL,vblank,NULL))return 9;
 while(ns()<deadline) {
  struct pollfd p={.fd=input,.events=POLLIN};if(poll(&p,1,10)<=0)continue;struct input_event events[128];ssize_t bytes=read(input,events,sizeof(events));if(bytes<0){if(errno==EAGAIN)continue;break;}
  for(size_t j=0;j<(size_t)bytes/sizeof(events[0]);j++){
   struct input_event*e=&events[j];if(e->type==EV_KEY&&e->code==BTN_TOUCH)touching=!!e->value;
   if(e->type==EV_SYN&&e->code==SYN_DROPPED)dropped++;
   if(e->type!=EV_SYN||e->code!=SYN_REPORT)continue;frames++;
   uint64_t t=(uint64_t)e->time.tv_sec*1000000000+(uint64_t)e->time.tv_usec*1000,now=ns();
   if(touching){touchframes++;if(was)gap(&touch,t);else touch.previous=t;if(now>=t)add(&age,now-t);}else touch.previous=0;
   was=touching;
  }
 }
 pthread_join(thread,NULL);printf("TOUCH_SUMMARY frames=%u touchframes=%u syn_dropped=%u no_grab=1 no_inject=1\n",frames,touchframes,dropped);
 printstats("TOUCH_ACTIVE_REPORT_GAP",&touch);printstats("EVDEV_READ_AGE",&age);close(input);close(card);return 0;
}
