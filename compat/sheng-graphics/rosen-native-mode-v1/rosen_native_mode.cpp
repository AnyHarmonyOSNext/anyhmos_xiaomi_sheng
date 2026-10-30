// Calls unmodified ROM RsVulkanContext and Drawing surface factories.
#include <cstdio>
#include <cstdint>
#include <dlfcn.h>
#include <unistd.h>
#include <memory>
#include <string>
#include <vector>
#include <signal.h>
#include <ucontext.h>
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
 auto *rsMode=(int*)dlsym(lib,"_ZN4OHOS5Rosen18RSSystemProperties17systemGpuApiType_E");CHECK(drawingMode&&rsMode);printf("NATIVE_MODE drawing=%d rs=%d global_override=0\n",*drawingMode,*rsMode);CHECK(*drawingMode==1&&*rsMode==1);
std::string cache="";puts("BEFORE_CONTEXT");auto rs=singleton(cache);CHECK(rs);auto gpu=context(rs,cache);CHECK(gpu);puts("ORIGINAL_ROSEN_GPU_CONTEXT=1");
 ImageInfo info{128,96,4,2,{}};auto surface=make(gpu.get(),false,info);CHECK(surface);auto c=canvas(surface.get());CHECK(c);clear(c.get(),0xff00ff00);std::vector<uint32_t> pixels(128*96+32,0x13579bdf);CHECK(read(c.get(),info,pixels.data(),512,0,0));for(int i=0;i<128*96;i++)CHECK(pixels[i]==0xff00ff00);for(int i=128*96;i<int(pixels.size());i++)CHECK(pixels[i]==0x13579bdf);puts("ROSEN_GPU_CONTRACT=0 native_context=1 native_gpu_surface=1 pixels=12288 guard_words=32");_exit(0);}
