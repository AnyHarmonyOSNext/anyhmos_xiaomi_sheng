// Calls unmodified ROM RsVulkanContext and Drawing surface factories.
#include <cstdio>
#include <cstdint>
#include <dlfcn.h>
#include <fcntl.h>
#include <sys/ioctl.h>
#include <sys/mman.h>
#include <linux/dma-buf.h>
#include <linux/dma-heap.h>
#include <cstring>
#include <unistd.h>
#include <memory>
#include <native_buffer/native_buffer.h>
#include <cstdlib>
#include <string>
#include <vector>
#include <signal.h>
#include <ucontext.h>
struct Handle {int32_t fd,width,stride,height,size,format;uint64_t usage;void*vir;uint64_t phy;uint32_t fds,ints;};
struct Ref {void*p;~Ref(){}};
struct Backend {alignas(8) char data[128];~Backend(){}};
struct Format {int color,alpha;};
struct Sampling {bool cubic=false;float b=0,c=0;int filter=0,mipmap=0;};
struct ImageInfo {int width,height,color,alpha;std::shared_ptr<void> colorSpace;};
#define CHECK(x) do{if(!(x)){printf("FAIL line=%d %s\n",__LINE__,#x);return 1;}}while(0)
static void crash(int,siginfo_t*,void*u){auto*c=(ucontext_t*)u;Dl_info d{};dladdr((void*)c->uc_mcontext.pc,&d);printf("CRASH pc=%p lib=%s offset=%lx lr=%llx\n",(void*)c->uc_mcontext.pc,d.dli_fname?d.dli_fname:"?",c->uc_mcontext.pc-(uintptr_t)d.dli_fbase,(unsigned long long)c->uc_mcontext.regs[30]);_exit(2);}
int main(int argc,char**argv){setbuf(stdout,nullptr);alarm(40);struct sigaction sa{};sa.sa_sigaction=crash;sa.sa_flags=SA_SIGINFO;sigaction(SIGSEGV,&sa,nullptr);puts("BEFORE_RS_LOAD");
 auto lib=dlopen("librender_service_base.z.so",RTLD_NOW|RTLD_GLOBAL);if(!lib){puts(dlerror());return 1;}
 auto singleton=(void*(*)(const std::string&))dlsym(lib,"_ZN4OHOS5Rosen15RsVulkanContext12GetSingletonERKNSt3__h12basic_stringIcNS2_11char_traitsIcEENS2_9allocatorIcEEEE");
 auto context=(std::shared_ptr<void>(*)(void*,const std::string&))dlsym(lib,"_ZN4OHOS5Rosen15RsVulkanContext17GetDrawingContextERKNSt3__h12basic_stringIcNS2_11char_traitsIcEENS2_9allocatorIcEEEE");
 auto make=(std::shared_ptr<void>(*)(void*,bool,const ImageInfo&))dlsym(lib,"_ZN4OHOS5Rosen7Drawing7Surface16MakeRenderTargetEPNS1_10GPUContextEbRKNS1_9ImageInfoE");
 auto canvas=(std::shared_ptr<void>(*)(void*))dlsym(lib,"_ZN4OHOS5Rosen7Drawing7Surface9GetCanvasEv");
 auto clear=(void(*)(void*,uint32_t))dlsym(lib,"_ZN4OHOS5Rosen7Drawing10CoreCanvas5ClearEj");
 auto read=(bool(*)(void*,const ImageInfo&,void*,size_t,int,int))dlsym(lib,"_ZN4OHOS5Rosen7Drawing10CoreCanvas10ReadPixelsERKNS1_9ImageInfoEPvmii");
 CHECK(singleton&&context&&make&&canvas&&clear&&read);
 auto *drawingMode=(int*)dlsym(lib,"_ZN4OHOS5Rosen7Drawing16SystemProperties17systemGpuApiType_E");
 auto *rsMode=(int*)dlsym(lib,"_ZN4OHOS5Rosen18RSSystemProperties17systemGpuApiType_E");CHECK(drawingMode&&rsMode);printf("MODE_FIXTURE original_drawing=%d original_rs=%d selected_vulkan=1\n",*drawingMode,*rsMode);*drawingMode=1;*rsMode=1;
std::string cache="";puts("BEFORE_CONTEXT");auto rs=singleton(cache);CHECK(rs);auto gpu=context(rs,cache);CHECK(gpu);puts("ORIGINAL_ROSEN_GPU_CONTEXT=1");

 void*native=dlopen("libnative_buffer.so",RTLD_NOW|RTLD_GLOBAL);CHECK(native);
 void*window=dlopen("libnative_window.so",RTLD_NOW|RTLD_GLOBAL);CHECK(window);
 auto nw=(void*(*)(void*))dlsym(window,"OH_NativeWindow_CreateNativeWindowBufferFromNativeBuffer");CHECK(nw);
 auto backend=(Backend(*)(void*,int,int,bool))dlsym(lib,"_ZN4OHOS5Rosen17NativeBufferUtils34MakeBackendTextureFromNativeBufferEP18NativeWindowBufferiib");CHECK(backend);
 auto valid=(bool(*)(const void*))dlsym(lib,"_ZNK4OHOS5Rosen7Drawing14BackendTexture7IsValidEv");CHECK(valid);
 auto tex=(const void*(*)(const void*))dlsym(lib,"_ZNK4OHOS5Rosen7Drawing14BackendTexture14GetTextureInfoEv");CHECK(tex);
 auto ctor=(void(*)(void*))dlsym(lib,"_ZN4OHOS5Rosen7Drawing5ImageC1Ev");CHECK(ctor);
 auto build=(bool(*)(void*,void*,const void*,int,Format,const std::shared_ptr<void>&,void(*)(void*),void*,bool))dlsym(lib,"_ZN4OHOS5Rosen7Drawing5Image16BuildFromTextureERNS1_10GPUContextERKNS1_11TextureInfoENS1_13TextureOriginENS1_12BitmapFormatERKNSt3__h10shared_ptrINS1_10ColorSpaceEEEPFvPvESG_b");CHECK(build);
 auto draw=(void(*)(void*,const void*,float,float,const Sampling&))dlsym(lib,"_ZN4OHOS5Rosen7Drawing10CoreCanvas9DrawImageERKNS1_5ImageEffRKNS1_15SamplingOptionsE");CHECK(draw);
 constexpr int W=128,H=96,logical=W*H*3/2;
 int format=argc>1?atoi(argv[1]):29;CHECK(format==24||format==28||format==29);
 auto alloc=(decltype(&OH_NativeBuffer_Alloc))dlsym(native,"OH_NativeBuffer_Alloc");
 auto handle=(const Handle*(*)(OH_NativeBuffer*))dlsym(native,"OH_NativeBuffer_GetBufferHandle");CHECK(alloc&&handle);
 OH_NativeBuffer_Config config{W,H,format,0x42b,0};auto *nativeBuffer=alloc(&config);CHECK(nativeBuffer);
 auto*h=handle(nativeBuffer);CHECK(h&&h->stride==W);int total=h->size;
 printf("REAL_NATIVE_ALLOCATION format=%d stride=%d size=%d\n",format,h->stride,total);
 auto*input=(unsigned char*)mmap(nullptr,total,PROT_READ|PROT_WRITE,MAP_SHARED,h->fd,0);CHECK(input!=MAP_FAILED);
 dma_buf_sync sync{DMA_BUF_SYNC_START|DMA_BUF_SYNC_RW};CHECK(!ioctl(h->fd,DMA_BUF_IOCTL_SYNC,&sync));
 memset(input,0xcd,logical);
 const unsigned char yuv[3][3]={{81,90,240},{145,54,34},{41,240,110}};
 for(int y=0;y<H;y++)for(int x=0;x<W;x++)input[y*W+x]=yuv[x<42?0:x<84?1:2][0];
 for(int y=0;y<H/2;y++)for(int x=0;x<W/2;x++) {
  int band=x*2<42?0:x*2<84?1:2;
  if(format==24){input[W*H+y*W+x*2]=yuv[band][1];input[W*H+y*W+x*2+1]=yuv[band][2];}
  else {input[W*H+y*(W/2)+x]=yuv[band][format==29?2:1];input[W*H+W*H/4+y*(W/2)+x]=yuv[band][format==29?1:2];}
 }
 sync.flags=DMA_BUF_SYNC_END|DMA_BUF_SYNC_RW;CHECK(!ioctl(h->fd,DMA_BUF_IOCTL_SYNC,&sync));
 void*buf=nw(nativeBuffer);CHECK(buf);puts("BEFORE_NV12_BACKEND");auto bt=backend(buf,W,H,false);printf("NV12_BACKEND_VALID=%d\n",valid(&bt));CHECK(valid(&bt));
 const void *ti=tex(&bt);CHECK(ti);
 // Read-only inspection of the pinned donor TextureInfo shared-pointer field.
 auto *vkBytes=*(const unsigned char *const*)((const char*)ti+24);CHECK(vkBytes);
 for(int off=0;off<160;off+=16){printf("VK_TEXTURE_WORDS offset=%d",off);for(int k=0;k<16;k+=4){uint32_t v;memcpy(&v,vkBytes+off+k,4);printf(" %08x",v);}puts("");}
 struct Opaque {alignas(8) char bytes[512];~Opaque(){}};
 void *two=dlopen("lib2d_graphics.z.so",RTLD_NOW|RTLD_LOCAL);
 void *sk=dlopen("libskia_canvaskit.z.so",RTLD_NOW|RTLD_LOCAL);CHECK(two&&sk);
 auto convert=(Opaque(*)(const void*))dlsym(two,"_ZN4OHOS5Rosen7Drawing15SkiaTextureInfo27ConvertToGrBackendVKTextureERKNS1_11TextureInfoE");
 auto getFormat=(Opaque(*)(const void*))dlsym(sk,"_ZNK16GrBackendTexture16getBackendFormatEv");
 auto getGr=(Ref(*)(const void*))dlsym(two,"_ZNK4OHOS5Rosen7Drawing14SkiaGPUContext12GetGrContextEv");
 auto caps=(const void*(*)(const void*))dlsym(sk,"_ZNK14GrContext_Base4capsEv");
 auto texturable=(bool(*)(const void*,const void*,int))dlsym(sk,"_ZNK8GrVkCaps18isFormatTexturableERK15GrBackendFormat13GrTextureType");
 CHECK(convert&&getFormat&&getGr&&caps&&texturable);
 auto backendInfo=convert(ti);auto backendFormat=getFormat(&backendInfo);
 auto direct=getGr(*(void**)gpu.get());CHECK(direct.p);auto *cap=caps(direct.p);CHECK(cap);
 printf("SKIA_FORMAT_TEXTURABLE=%d\n",texturable(cap,&backendFormat,1));
 alignas(16) char img[512]={};ctor(img);std::shared_ptr<void> cs;bool ok=build(img,gpu.get(),tex(&bt),0,Format{4,1},cs,nullptr,nullptr,false);printf("NV12_DRAWING_IMAGE=%d\n",ok);CHECK(ok);
 ImageInfo info{W,H,4,2,{}};auto surface=make(gpu.get(),false,info);CHECK(surface);auto c=canvas(surface.get());CHECK(c);clear(c.get(),0xff000000);Sampling sampling;draw(c.get(),img,0,0,sampling);
 std::vector<uint32_t> pixels(W*H+32,0x13579bdf);CHECK(read(c.get(),info,pixels.data(),W*4,0,0)); int good=0;
 for(int i=0;i<W*H;i++){
  int x=i%W,band=x<42?0:x<84?1:2;bool accurate=true;
  // Chroma reconstruction filters the two band boundaries. Compare solid
  // interiors identically for the NV12 baseline and both planar formats.
  if((x>=40&&x<=43)||(x>=82&&x<=85))continue;
  for(int ch=0;ch<4;ch++){int expected=ch==3||ch==band?255:0;int delta=int((pixels[i]>>(ch*8))&255)-expected;if(delta<0)delta=-delta;if(delta>4)accurate=false;}
  if(accurate)good++;
 }
 printf("YUV_COLOR_PIXELS=%d expected=%d format=%d first=%08x mid=%08x last=%08x\n",good,(W-8)*H,format,pixels[0],pixels[64],pixels[127]);CHECK(good==(W-8)*H);
 for(int i=W*H;i<int(pixels.size());i++)CHECK(pixels[i]==0x13579bdf);sync.flags=DMA_BUF_SYNC_START|DMA_BUF_SYNC_READ;CHECK(ioctl(h->fd,DMA_BUF_IOCTL_SYNC,&sync)==0);sync.flags=DMA_BUF_SYNC_END|DMA_BUF_SYNC_READ;CHECK(ioctl(h->fd,DMA_BUF_IOCTL_SYNC,&sync)==0);puts("ROSEN_YUV_CONTRACT=0");_exit(0);}
