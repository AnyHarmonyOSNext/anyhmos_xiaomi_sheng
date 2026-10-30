/* Read current linear KMS framebuffer. No modeset, draw, plane or image edits. */
#define _GNU_SOURCE
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <unistd.h>
#include <errno.h>
#include <fcntl.h>
#include <sys/ioctl.h>
#include <sys/mman.h>
#include <drm/drm.h>
#include <drm/drm_mode.h>
#include <drm/drm_fourcc.h>
#include <linux/dma-buf.h>
static int writeall(int fd,const void *data,size_t n){const char*p=data;while(n){ssize_t z=write(fd,p,n);if(z<0&&errno==EINTR)continue;if(z<=0)return -1;p+=z;n-=z;}return 0;}
int main(int argc,char**argv){
 if(argc!=2&&argc!=3)return 2;
 unsigned step=argc==3?(unsigned)strtoul(argv[2],NULL,10):1;
 if(!step||step>16)return 2;
 int drm=open("/dev/dri/card0",O_RDWR|O_CLOEXEC);if(drm<0){perror("drm");return 3;}
 struct drm_set_client_cap cap={.capability=DRM_CLIENT_CAP_UNIVERSAL_PLANES,.value=1};
 if(ioctl(drm,DRM_IOCTL_SET_CLIENT_CAP,&cap)){perror("client cap");return 4;}
 struct drm_mode_get_plane plane={.plane_id=90};
 if(ioctl(drm,DRM_IOCTL_MODE_GETPLANE,&plane)||!plane.fb_id){perror("plane fb");return 5;}
 struct drm_mode_fb_cmd2 fb={.fb_id=plane.fb_id};
 if(ioctl(drm,DRM_IOCTL_MODE_GETFB2,&fb)){perror("GETFB2");return 6;}
 fprintf(stderr,"SCANOUT_CAPTURE plane=%u fb=%u width=%u height=%u pitch=%u format=%08x modifier=%llx offset=%u\n",plane.plane_id,fb.fb_id,fb.width,fb.height,fb.pitches[0],fb.pixel_format,(unsigned long long)fb.modifier[0],fb.offsets[0]);
 int rgba=fb.pixel_format==DRM_FORMAT_ABGR8888||fb.pixel_format==DRM_FORMAT_XBGR8888;
 int bgra=fb.pixel_format==DRM_FORMAT_ARGB8888||fb.pixel_format==DRM_FORMAT_XRGB8888;
 if((!rgba&&!bgra)||fb.modifier[0]!=DRM_FORMAT_MOD_LINEAR||!fb.handles[0]||fb.width>16384||fb.height>16384||!fb.width||!fb.height||fb.pitches[0]<fb.width*4)return 7;
 struct drm_prime_handle prime={.handle=fb.handles[0],.flags=DRM_CLOEXEC|DRM_RDWR,.fd=-1};
 if(ioctl(drm,DRM_IOCTL_PRIME_HANDLE_TO_FD,&prime)){perror("PRIME export");return 8;}
 size_t size=(size_t)fb.offsets[0]+(size_t)fb.pitches[0]*fb.height;
 const unsigned char *map=mmap(NULL,size,PROT_READ,MAP_SHARED,prime.fd,0);
 if(map==MAP_FAILED){perror("mmap");return 9;}
 struct dma_buf_sync sync={.flags=DMA_BUF_SYNC_START|DMA_BUF_SYNC_READ};
 if(ioctl(prime.fd,DMA_BUF_IOCTL_SYNC,&sync)){perror("sync start");return 10;}
 int output=open(argv[1],O_WRONLY|O_CREAT|O_EXCL|O_CLOEXEC,0600);if(output<0){perror("output");return 11;}
 unsigned width=(fb.width+step-1)/step,height=(fb.height+step-1)/step;
 char header[100];int n=snprintf(header,sizeof(header),"P6\n%u %u\n255\n",width,height);
 if(writeall(output,header,n))return 12;
 unsigned char *row=malloc((size_t)width*3);if(!row)return 13;
 for(unsigned y=0;y<fb.height;y+=step){
  const unsigned char *src=map+fb.offsets[0]+(size_t)y*fb.pitches[0];
  for(unsigned x=0,j=0;x<fb.width;x+=step,j++){row[j*3]=src[x*4+(rgba?0:2)];row[j*3+1]=src[x*4+1];row[j*3+2]=src[x*4+(rgba?2:0)];}
  if(writeall(output,row,(size_t)width*3))return 14;
 }
 close(output);free(row);sync.flags=DMA_BUF_SYNC_END|DMA_BUF_SYNC_READ;
 if(ioctl(prime.fd,DMA_BUF_IOCTL_SYNC,&sync)){perror("sync end");return 15;}
 munmap((void*)map,size);close(prime.fd);close(drm);
 fprintf(stderr,"SCANOUT_CAPTURE_OK source=actual_KMS_DMA_BUF no_modeset=1 step=%u output=%ux%u\n",step,width,height);return 0;
}
