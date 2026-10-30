// SPDX-License-Identifier: MIT
// Bounded diagnostic: use the existing original audio_server token, never mint one.
#include <cstdio>
#include <cstdint>
#include <cstdlib>
#include <cstring>
#include <string>
#include <dlfcn.h>
#include <grp.h>
#include <unistd.h>
#include <sys/prctl.h>

int main(int argc,char **argv)
{
    bool play_file=argc==2 && !strcmp(argv[1],"file");
    alarm(play_file?70:25); setbuf(stdout,nullptr); setbuf(stderr,nullptr);
    void *sdk=dlopen("libnativetoken_shared.z.so",RTLD_NOW|RTLD_LOCAL);
    void *proc=dlopen("libtokensetproc_shared.z.so",RTLD_NOW|RTLD_LOCAL);
    if (!sdk || !proc) { printf("AUDIO_IDENTITY_LOAD_ERROR=%s\n",dlerror()); return 2; }
    auto set=reinterpret_cast<int (*)(uint64_t)>(dlsym(proc,"SetSelfTokenID"));
    auto parse=reinterpret_cast<void *(*)(const char *)>(dlsym(sdk,"cJSON_Parse"));
    auto count=reinterpret_cast<int (*)(const void *)>(dlsym(sdk,"cJSON_GetArraySize"));
    auto item=reinterpret_cast<void *(*)(const void *,int)>(dlsym(sdk,"cJSON_GetArrayItem"));
    auto field=reinterpret_cast<void *(*)(const void *,const char *)>(dlsym(sdk,"cJSON_GetObjectItemCaseSensitive"));
    auto text=reinterpret_cast<char *(*)(const void *)>(dlsym(sdk,"cJSON_GetStringValue"));
    auto number=reinterpret_cast<double (*)(const void *)>(dlsym(sdk,"cJSON_GetNumberValue"));
    auto destroy=reinterpret_cast<void (*)(void *)>(dlsym(sdk,"cJSON_Delete"));
    if (!set || !parse || !count || !item || !field || !text || !number || !destroy) return 3;
    FILE *file=fopen("/data/service/el0/access_token/nativetoken.json","re");
    if (!file) return 3;
    char buf[131072]; size_t len=fread(buf,1,sizeof(buf)-1,file); fclose(file); buf[len]=0;
    if (len==sizeof(buf)-1) return 3;
    void *root=parse(buf); if (!root) return 3;
    uint32_t token=0; unsigned found=0;
    for (int i=0;i<count(root);i++) {
        void *entry=item(root,i); const char *name=text(field(entry,"processName"));
        if (name && !strcmp(name,"audio_server") && number(field(entry,"uid"))==1041) {
            double id=number(field(entry,"tokenId"));
            if (id>0 && id<=UINT32_MAX) { token=(uint32_t)id; found++; }
        }
    }
    destroy(root);
    if (found!=1) return 4;
    printf("AUDIO_EXISTING_TOKEN=%u\n",token);
    if (!token) return 4;
    if (argc>1 && !strcmp(argv[1],"check")) return 0;
    int rc=set(token); printf("AUDIO_SET_EXISTING_TOKEN_RC=%d\n",rc);
    if (rc) return 5;
    // Match the imported original init profile's IDs by their actual group names.
    const char *names[]={"system","audio","input","ueventd","usb_host","data_reserve"};
    gid_t gids[6];
    for (unsigned i=0;i<6;i++) { auto g=getgrnam(names[i]); if (!g) return 6; gids[i]=g->gr_gid; }
    if (setgroups(6,gids) || setgid(gids[0]) || setuid(1041)) { perror("audio identity"); return 7; }
    printf("AUDIO_DIAGNOSTIC_IDENTITY uid=%d gid=%d\n",getuid(),getgid());
    if (setenv("LD_PRELOAD","/compat/lib64/libsheng_audio_vdi_loader.so",1) ||
        setenv("PULSE_RUNTIME_PATH","/data/data/.pulse_dir/runtime",1) ||
        setenv("PULSE_STATE_PATH","/data/data/.pulse_dir/state",1)) return 8;
    if (argc>1 && !strcmp(argv[1],"host")) {
        execl("/data/local/tmp/native_audio_hdi_publisher","native_audio_hdi_publisher",(char *)nullptr);
    } else if (argc>1 && !strcmp(argv[1],"renderer")) {
        execl("/data/local/tmp/native_system_audio_check","native_system_audio_check",(char *)nullptr);
    } else if (play_file) {
        execl("/data/local/tmp/native_audio_file_player","native_audio_file_player","/data/local/tmp/canyue.mp3",(char *)nullptr);
    } else execl("/system/bin/sa_main","sa_main","/system/profile/audio_server.json",(char *)nullptr);
    perror("audio sa_main exec"); return 9;
}
