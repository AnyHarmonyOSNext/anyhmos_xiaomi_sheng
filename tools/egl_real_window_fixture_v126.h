// Uses real Surface/HDI allocation; no injected handles or private offsets.
#include <native_image/native_image.h>
#include <native_window/external_window.h>
#include <native_buffer/native_buffer.h>
#include <poll.h>
#define WCHECK(x) do { if (!(x)) { printf("WINDOW_FAIL line=%d %s\n", __LINE__, #x); return 1; } } while (0)
#define WLOAD(h,n) auto n = (decltype(&::n))dlsym(h,#n); WCHECK(n)
struct WindowFixture {
 OHNativeWindow *window = nullptr;
 OH_NativeImage *image = nullptr;
 void *imageLib = nullptr, *windowLib = nullptr, *bufferLib = nullptr;
 int Init() {
  imageLib=dlopen("libnative_image.so",RTLD_NOW|RTLD_LOCAL); WCHECK(imageLib);
  windowLib=dlopen("libnative_window.so",RTLD_NOW|RTLD_LOCAL); WCHECK(windowLib);
  bufferLib=dlopen("libnative_buffer.so",RTLD_NOW|RTLD_LOCAL); WCHECK(bufferLib);
  WLOAD(imageLib,OH_ConsumerSurface_Create);
  WLOAD(imageLib,OH_ConsumerSurface_SetDefaultSize);
  WLOAD(imageLib,OH_ConsumerSurface_SetDefaultUsage);
  WLOAD(imageLib,OH_NativeImage_AcquireNativeWindow);
  WLOAD(imageLib,OH_NativeImage_SetOnFrameAvailableListener);
  WLOAD(windowLib,OH_NativeWindow_NativeWindowHandleOpt);
  image=OH_ConsumerSurface_Create(); WCHECK(image);
  WCHECK(!OH_ConsumerSurface_SetDefaultSize(image,32,32));
  WCHECK(!OH_ConsumerSurface_SetDefaultUsage(image,0x70b));
  WCHECK(!OH_NativeImage_SetOnFrameAvailableListener(image,{nullptr,[](void*){}}));
  window=OH_NativeImage_AcquireNativeWindow(image); WCHECK(window);
  WCHECK(!OH_NativeWindow_NativeWindowHandleOpt(window,SET_BUFFER_GEOMETRY,32,32));
  WCHECK(!OH_NativeWindow_NativeWindowHandleOpt(window,SET_FORMAT,12));
  WCHECK(!OH_NativeWindow_NativeWindowHandleOpt(window,SET_USAGE,uint64_t(0x70b)));
  puts("REAL_ALLOCATOR_WINDOW_READY"); return 0;
 }
 int CheckGreen() {
  WLOAD(imageLib,OH_NativeImage_AcquireNativeWindowBuffer);
  WLOAD(imageLib,OH_NativeImage_ReleaseNativeWindowBuffer);
  WLOAD(windowLib,OH_NativeWindow_GetBufferHandleFromNative);
  WLOAD(bufferLib,OH_NativeBuffer_FromNativeWindowBuffer);
  WLOAD(bufferLib,OH_NativeBuffer_Map); WLOAD(bufferLib,OH_NativeBuffer_Unmap);
  OHNativeWindowBuffer *buffer=nullptr; int fence=-1, result=-1;
  for (int i=0;i<200;i++) {
   result=OH_NativeImage_AcquireNativeWindowBuffer(image,&buffer,&fence);
   if (!result) break;
   usleep(10000);
  }
  printf("REAL_ACQUIRE result=%d buffer=%p fence=%d\n",result,(void*)buffer,fence);
  WCHECK(!result && buffer);
  if (fence>=0) { pollfd p{fence,POLLIN,0}; int r=poll(&p,1,3000); close(fence); WCHECK(r>0&&(p.revents&POLLIN)); }
  auto *h=OH_NativeWindow_GetBufferHandleFromNative(buffer); WCHECK(h);
  printf("REAL_HANDLE width=%d height=%d stride=%d size=%d format=%d\n",h->width,h->height,h->stride,h->size,h->format);
  OH_NativeBuffer *native=nullptr; void *address=nullptr;
  int rc=OH_NativeBuffer_FromNativeWindowBuffer(buffer,&native);
  if (!rc) rc=OH_NativeBuffer_Map(native,&address);
  bool valid=!rc && address && h->width==32 && h->height==32 && h->stride>=128 && h->size>=h->stride*32 && h->format==12;
  int good=0;
  if (valid) for(int y=0;y<32;y++) for(int x=0;x<32;x++) {
   auto *p=(unsigned char*)address+y*h->stride+x*4;
   if(p[0]==0 && p[1]==255 && p[2]==0 && p[3]==255) good++;
  }
  if(!rc && address) OH_NativeBuffer_Unmap(native);
  int release=OH_NativeImage_ReleaseNativeWindowBuffer(image,buffer,-1);
  printf("REAL_WINDOW_PIXELS green=%d expected=1024 release=%d\n",good,release);
  WCHECK(valid && good==1024 && !release);
  puts("EGL_REAL_NATIVE_WINDOW_CONTRACT=0"); return 0;
 }
 ~WindowFixture() {
  if(image && imageLib) {
   auto destroy=(decltype(&::OH_NativeImage_Destroy))dlsym(imageLib,"OH_NativeImage_Destroy");
   if(destroy) destroy(&image);
  }
 }
};
#undef WCHECK
#undef WLOAD
