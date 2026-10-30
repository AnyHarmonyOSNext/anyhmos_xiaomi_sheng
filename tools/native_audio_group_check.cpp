// Read-only volume-group construction, bounded in a process separate from UI.
#include <cstdio>
#include <dlfcn.h>
#include <memory>
#include <time.h>
#include <unistd.h>
namespace OHOS::AudioStandard { class AudioGroupManager; }
int main(int argc,char **argv)
{
 alarm(8);setbuf(stdout,nullptr);
 void *lib=dlopen(argc>1?argv[1]:"libaudio_policy_manager.z.so",RTLD_NOW|RTLD_LOCAL);
 if(!lib){printf("AUDIO_GROUP_LOAD_ERROR %s\n",dlerror());return 2;}
 auto instance=reinterpret_cast<void *(*)()>(dlsym(lib,"_ZN4OHOS13AudioStandard24AudioVolumeClientManager11GetInstanceEv"));
 auto group=reinterpret_cast<std::shared_ptr<OHOS::AudioStandard::AudioGroupManager>(*)(void *,int)>(dlsym(lib,"_ZN4OHOS13AudioStandard24AudioVolumeClientManager15GetGroupManagerEi"));
 if(!instance||!group){printf("AUDIO_GROUP_SYMBOL_ERROR %s\n",dlerror());return 3;}
 struct timespec a,b;clock_gettime(CLOCK_MONOTONIC,&a);
 for(int i=0;i<2;i++){auto g=group(instance(),0);printf("AUDIO_GROUP_CALL iteration=%d present=%d\n",i,g!=nullptr);}
 clock_gettime(CLOCK_MONOTONIC,&b);printf("AUDIO_GROUP_DIAGNOSTIC elapsed=%.6f\n",b.tv_sec-a.tv_sec+(b.tv_nsec-a.tv_nsec)/1e9);
 return 0;
}
