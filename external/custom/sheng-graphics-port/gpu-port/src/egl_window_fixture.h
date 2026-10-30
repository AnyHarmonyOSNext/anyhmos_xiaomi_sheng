// Recovery-only fixture using the original OHOS producer/consumer queue.
// No HDI allocator is available: install independently allocated DMA handles
// into the pinned ROM's SurfaceBuffer field. Never use this in production.
#include <native_image/native_image.h>
#include <native_window/external_window.h>
#include <native_buffer/native_buffer.h>
#include <fcntl.h>
#include <poll.h>
#include <sys/mman.h>
#include <sys/ioctl.h>
#include <linux/dma-buf.h>
#include <linux/dma-heap.h>
#include <cstdlib>
struct FixtureRef {void*p;~FixtureRef(){}};
struct FixtureHandle {int32_t fd,width,stride,height,size,format;uint64_t usage;void*virAddr;uint64_t phyAddr;uint32_t reserveFds,reserveInts;};
struct FixtureConfig {int32_t width,height,strideAlignment,format;uint64_t usage;int32_t timeout,colorGamut,transform;};
#define WCHECK(x) do{if(!(x)){printf("WINDOW_FAIL line=%d %s\n",__LINE__,#x);return 1;}}while(0)
#define WLOAD(h,n) auto n=(decltype(&::n))dlsym(h,#n);WCHECK(n)
struct WindowFixture {
 OHNativeWindow *window=nullptr;OH_NativeImage*image=nullptr;void*imageLib=nullptr;void*windowLib=nullptr;
 int Init(){
  imageLib=dlopen("libnative_image.so",RTLD_NOW|RTLD_LOCAL);if(!imageLib){puts(dlerror());return 1;}
  windowLib=dlopen("libnative_window.so",RTLD_NOW|RTLD_LOCAL);WCHECK(windowLib);
  WLOAD(imageLib,OH_ConsumerSurface_Create);WLOAD(imageLib,OH_ConsumerSurface_SetDefaultSize);WLOAD(imageLib,OH_ConsumerSurface_SetDefaultUsage);WLOAD(imageLib,OH_NativeImage_AcquireNativeWindow);WLOAD(imageLib,OH_NativeImage_SetOnFrameAvailableListener);
  WLOAD(windowLib,OH_NativeWindow_NativeWindowHandleOpt);WLOAD(windowLib,OH_NativeWindow_CreateNativeWindowBufferFromNativeBuffer);WLOAD(windowLib,OH_NativeWindow_NativeWindowAttachBuffer);WLOAD(windowLib,OH_NativeWindow_NativeWindowAbortBuffer);
  image=OH_ConsumerSurface_Create();WCHECK(image);WCHECK(!OH_ConsumerSurface_SetDefaultSize(image,32,32));WCHECK(!OH_ConsumerSurface_SetDefaultUsage(image,0x70b));WCHECK(!OH_NativeImage_SetOnFrameAvailableListener(image,{nullptr,[](void*){}}));window=OH_NativeImage_AcquireNativeWindow(image);WCHECK(window);
  WCHECK(!OH_NativeWindow_NativeWindowHandleOpt(window,SET_BUFFER_GEOMETRY,32,32));WCHECK(!OH_NativeWindow_NativeWindowHandleOpt(window,SET_FORMAT,12));WCHECK(!OH_NativeWindow_NativeWindowHandleOpt(window,SET_USAGE,uint64_t(0x70b)));
  void*n=dlopen("libnative_buffer.so",RTLD_NOW|RTLD_LOCAL);WCHECK(n);auto create=(FixtureRef(*)())dlsym(n,"_ZN4OHOS13SurfaceBuffer6CreateEv");auto config=(void(*)(void*,const FixtureConfig&))dlsym(n,"_ZN4OHOS17SurfaceBufferImpl22SetBufferRequestConfigERKNS_19BufferRequestConfigE");auto width=(void(*)(void*,int))dlsym(n,"_ZN4OHOS17SurfaceBufferImpl21SetSurfaceBufferWidthEi");auto height=(void(*)(void*,int))dlsym(n,"_ZN4OHOS17SurfaceBufferImpl22SetSurfaceBufferHeightEi");WCHECK(create&&config&&width&&height);
  for(int i=0;i<3;i++){
   int heap=open("/dev/dma_heap/system",O_RDONLY|O_CLOEXEC);WCHECK(heap>=0);dma_heap_allocation_data a{};a.len=8192;a.fd_flags=O_RDWR|O_CLOEXEC;WCHECK(!ioctl(heap,DMA_HEAP_IOCTL_ALLOC,&a));close(heap);
   auto*h=(FixtureHandle*)calloc(1,sizeof(FixtureHandle));h->fd=a.fd;h->width=h->height=32;h->stride=128;h->size=8192;h->format=12;h->usage=0x70b;
   auto*p=(unsigned char*)mmap(nullptr,8192,PROT_READ|PROT_WRITE,MAP_SHARED,h->fd,0);WCHECK(p!=MAP_FAILED);dma_buf_sync sync{DMA_BUF_SYNC_START|DMA_BUF_SYNC_RW};WCHECK(!ioctl(h->fd,DMA_BUF_IOCTL_SYNC,&sync));memset(p,0xcd,8192);sync.flags=DMA_BUF_SYNC_END|DMA_BUF_SYNC_RW;WCHECK(!ioctl(h->fd,DMA_BUF_IOCTL_SYNC,&sync));munmap(p,8192);
   auto owner=create();WCHECK(owner.p);WCHECK(!*(FixtureHandle**)((char*)owner.p+16));*(FixtureHandle**)((char*)owner.p+16)=h;FixtureConfig cfg{32,32,8,12,0x70b,0,0,0};config(owner.p,cfg);width(owner.p,32);height(owner.p,32);
   auto*b=OH_NativeWindow_CreateNativeWindowBufferFromNativeBuffer((OH_NativeBuffer*)owner.p);WCHECK(b);int rc=OH_NativeWindow_NativeWindowAttachBuffer(window,b);printf("ATTACH %d rc=%d\n",i,rc);WCHECK(!rc);rc=OH_NativeWindow_NativeWindowAbortBuffer(window,b);printf("ABORT %d rc=%d\n",i,rc);WCHECK(!rc);
  }puts("WINDOW_FIXTURE_READY");return 0;
 }
 int CheckGreen(){
  WLOAD(imageLib,OH_NativeImage_AcquireNativeWindowBuffer);WLOAD(imageLib,OH_NativeImage_ReleaseNativeWindowBuffer);WLOAD(windowLib,OH_NativeWindow_GetBufferHandleFromNative);
  OHNativeWindowBuffer*b=nullptr;int fence=-1;WCHECK(!OH_NativeImage_AcquireNativeWindowBuffer(image,&b,&fence));if(fence>=0){pollfd p{fence,POLLIN,0};WCHECK(poll(&p,1,5000)>0&&(p.revents&POLLIN));close(fence);}
  auto*h=(FixtureHandle*)OH_NativeWindow_GetBufferHandleFromNative(b);WCHECK(h&&h->width==32&&h->height==32&&h->stride==128);auto*p=(unsigned char*)mmap(nullptr,h->size,PROT_READ,MAP_SHARED,h->fd,0);WCHECK(p!=MAP_FAILED);dma_buf_sync sync{DMA_BUF_SYNC_START|DMA_BUF_SYNC_READ};WCHECK(!ioctl(h->fd,DMA_BUF_IOCTL_SYNC,&sync));for(int i=0;i<4096;i+=4)WCHECK(p[i]==0&&p[i+1]==255&&p[i+2]==0&&p[i+3]==255);for(int i=4096;i<8192;i++)WCHECK(p[i]==0xcd);sync.flags=DMA_BUF_SYNC_END|DMA_BUF_SYNC_READ;WCHECK(!ioctl(h->fd,DMA_BUF_IOCTL_SYNC,&sync));munmap(p,h->size);WCHECK(!OH_NativeImage_ReleaseNativeWindowBuffer(image,b,-1));puts("EGL_NATIVE_WINDOW_CONTRACT=0 pixels=1024 guard=4096");return 0;
 }
};
#undef WCHECK
#undef WLOAD
