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
int main(){setbuf(stdout,nullptr);alarm(40);struct sigaction sa{};sa.sa_sigaction=crash;sa.sa_flags=SA_SIGINFO;sigaction(SIGSEGV,&sa,nullptr);puts("BEFORE_RS_LOAD");
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
 auto create=(Ref(*)())dlsym(native,"_ZN4OHOS13SurfaceBuffer6CreateEv");CHECK(create);
 auto nw=(void*(*)(void*))dlsym(window,"OH_NativeWindow_CreateNativeWindowBufferFromNativeBuffer");CHECK(nw);
 auto backend=(Backend(*)(void*,int,int,bool))dlsym(lib,"_ZN4OHOS5Rosen17NativeBufferUtils34MakeBackendTextureFromNativeBufferEP18NativeWindowBufferiib");CHECK(backend);
 auto valid=(bool(*)(const void*))dlsym(lib,"_ZNK4OHOS5Rosen7Drawing14BackendTexture7IsValidEv");CHECK(valid);
 auto tex=(const void*(*)(const void*))dlsym(lib,"_ZNK4OHOS5Rosen7Drawing14BackendTexture14GetTextureInfoEv");CHECK(tex);
 auto ctor=(void(*)(void*))dlsym(lib,"_ZN4OHOS5Rosen7Drawing5ImageC1Ev");CHECK(ctor);
 auto build=(bool(*)(void*,void*,const void*,int,Format,const std::shared_ptr<void>&,void(*)(void*),void*,bool))dlsym(lib,"_ZN4OHOS5Rosen7Drawing5Image16BuildFromTextureERNS1_10GPUContextERKNS1_11TextureInfoENS1_13TextureOriginENS1_12BitmapFormatERKNSt3__h10shared_ptrINS1_10ColorSpaceEEEPFvPvESG_b");CHECK(build);
 auto draw=(void(*)(void*,const void*,float,float,const Sampling&))dlsym(lib,"_ZN4OHOS5Rosen7Drawing10CoreCanvas9DrawImageERKNS1_5ImageEffRKNS1_15SamplingOptionsE");CHECK(draw);
 constexpr int W=128,H=96,logical=W*H*3/2,total=logical+4096;
 int heap=open("/dev/dma_heap/system",O_RDONLY|O_CLOEXEC);CHECK(heap>=0);
 dma_heap_allocation_data req{};req.len=total;req.fd_flags=O_RDWR|O_CLOEXEC;CHECK(ioctl(heap,DMA_HEAP_IOCTL_ALLOC,&req)==0);close(heap);
 auto*h=(Handle*)calloc(1,sizeof(Handle));h->fd=req.fd;h->width=W;h->height=H;h->stride=W;h->size=total;h->format=24;h->usage=0x42b;
 auto*input=(unsigned char*)mmap(nullptr,total,PROT_READ|PROT_WRITE,MAP_SHARED,h->fd,0);CHECK(input!=MAP_FAILED);
 dma_buf_sync sync{DMA_BUF_SYNC_START|DMA_BUF_SYNC_RW};CHECK(ioctl(h->fd,DMA_BUF_IOCTL_SYNC,&sync)==0);
 memset(input,235,W*H);memset(input+W*H,128,W*H/2);memset(input+logical,0xcd,4096);
 sync.flags=DMA_BUF_SYNC_END|DMA_BUF_SYNC_RW;CHECK(ioctl(h->fd,DMA_BUF_IOCTL_SYNC,&sync)==0);
 auto owner=create();CHECK(owner.p);CHECK(*reinterpret_cast<Handle**>((char*)owner.p+16)==nullptr);*reinterpret_cast<Handle**>((char*)owner.p+16)=h;
 void*buf=nw(owner.p);CHECK(buf);puts("BEFORE_NV12_BACKEND");auto bt=backend(buf,W,H,false);printf("NV12_BACKEND_VALID=%d\n",valid(&bt));CHECK(valid(&bt));
 alignas(16) char img[512]={};ctor(img);std::shared_ptr<void> cs;bool ok=build(img,gpu.get(),tex(&bt),0,Format{4,1},cs,nullptr,nullptr,false);printf("NV12_DRAWING_IMAGE=%d\n",ok);CHECK(ok);
 ImageInfo info{W,H,4,2,{}};auto surface=make(gpu.get(),false,info);CHECK(surface);auto c=canvas(surface.get());CHECK(c);clear(c.get(),0xff000000);Sampling sampling;draw(c.get(),img,0,0,sampling);
 std::vector<uint32_t> pixels(W*H+32,0x13579bdf);CHECK(read(c.get(),info,pixels.data(),W*4,0,0));int white=0;for(int i=0;i<W*H;i++)if((pixels[i]&255)>=250&&((pixels[i]>>8)&255)>=250&&((pixels[i]>>16)&255)>=250)white++;
 printf("NV12_WHITE_PIXELS=%d total=%d first=%08x center=%08x\n",white,W*H,pixels[0],pixels[W*H/2]);
 for(int i=W*H;i<int(pixels.size());i++)CHECK(pixels[i]==0x13579bdf);CHECK(white==W*H);sync.flags=DMA_BUF_SYNC_START|DMA_BUF_SYNC_READ;CHECK(ioctl(h->fd,DMA_BUF_IOCTL_SYNC,&sync)==0);for(int i=logical;i<total;i++)CHECK(input[i]==0xcd);sync.flags=DMA_BUF_SYNC_END|DMA_BUF_SYNC_READ;CHECK(ioctl(h->fd,DMA_BUF_IOCTL_SYNC,&sync)==0);puts("ROSEN_YUV_CONTRACT=0");_exit(0);}
