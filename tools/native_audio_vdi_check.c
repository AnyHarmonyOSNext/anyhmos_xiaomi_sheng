/* Bounded original donor6.1 wrapper -> compatible VDI -> real stock PAL check. */
#include "iaudio_manager_vdi.h"
#include <dlfcn.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>

struct hdi_adapter {
    int (*InitAllPorts)(struct hdi_adapter *);
    int (*CreateRender)(struct hdi_adapter *,const struct AudioDeviceDescriptorVdi *,
        const struct AudioSampleAttributesVdi *,struct IAudioRenderVdi **,uint32_t *);
    int (*DestroyRender)(struct hdi_adapter *,uint32_t);
};
struct hdi_manager {
    int (*GetAllAdapters)(struct hdi_manager *,struct AudioAdapterDescriptorVdi *,uint32_t *);
    int (*LoadAdapter)(struct hdi_manager *,const struct AudioAdapterDescriptorVdi *,struct hdi_adapter **);
    int (*UnloadAdapter)(struct hdi_manager *,const char *);
};
static int one_stream(void *lib,struct hdi_adapter *a,unsigned format)
{
    struct AudioDeviceDescriptorVdi device={.portId=0,.pins=PIN_VDI_OUT_SPEAKER,.desc="Speaker"};
    struct AudioSampleAttributesVdi attrs={.type=AUDIO_VDI_IN_MEDIA,.interleaved=true,
        .format=format,.sampleRate=48000,.channelCount=2,.channelLayout=3,
        .period=240,.frameSize=format==4?8:4,.isSignedData=true};
    struct IAudioRenderVdi *s=0; uint32_t id=0;
    int rc=a->CreateRender(a,&device,&attrs,&s,&id);
    printf("AUDIO_VDI_CREATE format=%u rc=%d id=%u render=%p\n",format,rc,id,(void *)s);
    if (rc || !s) return 3;
    /* Check actual original wrapper addresses before calling the adapted table. */
    const struct {unsigned slot; const char *symbol;} checks[]={
        {1,"AudioRenderFrameVdi"},{12,"AudioRenderSetMuteVdi"},{14,"AudioRenderSetVolumeVdi"},
        {16,"AudioRenderGetVolumeVdi"},{20,"AudioRenderGetFrameSizeVdi"},
        {32,"AudioRenderStartVdi"},{33,"AudioRenderStopVdi"}};
    for (unsigned i=0;i<sizeof(checks)/sizeof(checks[0]);i++) {
        void *fn=dlsym(lib,checks[i].symbol);
        if (!fn || ((void **)s)[checks[i].slot]!=fn) {
            printf("AUDIO_VDI_TABLE_MISMATCH slot=%u name=%s\n",checks[i].slot,checks[i].symbol);
            (void)a->DestroyRender(a,id); return 4;
        }
    }
    uint64_t frame_size=0;
    rc=s->GetFrameSize(s,&frame_size);
    printf("AUDIO_VDI_FRAME_SIZE rc=%d bytes=%llu\n",rc,(unsigned long long)frame_size);
    if (!rc && frame_size!=attrs.frameSize) rc=-1;
    if (!rc) { rc=s->SetVolume(s,0.03f); printf("AUDIO_VDI_SET_VOLUME_RC=%d\n",rc); }
    if (!rc) { float v=0; rc=s->GetVolume(s,&v); printf("AUDIO_VDI_GET_VOLUME rc=%d volume=%.6f\n",rc,v); }
    if (!rc) { rc=s->Start(s); printf("AUDIO_VDI_START_RC=%d\n",rc); }
    char silence[1920]={0}; uint64_t total=0;
    unsigned bytes=format==4?1920:960;
    for (unsigned i=0;!rc && i<40;i++) {
        uint64_t wrote=0; rc=s->RenderFrame(s,(int8_t *)silence,bytes,&wrote);
        total+=wrote; if (!rc && wrote!=bytes) rc=-1;
    }
    printf("AUDIO_VDI_PCM format=%u rc=%d input_bytes=%llu\n",format,rc,(unsigned long long)total);
    int m=s->SetMute(s,true); printf("AUDIO_VDI_MUTE_RC=%d\n",m);
    bool muted=false; int g=s->GetMute(s,&muted); printf("AUDIO_VDI_GET_MUTE rc=%d value=%d\n",g,muted);
    int u=s->SetMute(s,false); printf("AUDIO_VDI_UNMUTE_RC=%d\n",u);
    int stop=s->Stop(s); printf("AUDIO_VDI_STOP_RC=%d\n",stop);
    int end=a->DestroyRender(a,id); printf("AUDIO_VDI_DESTROY_RC=%d\n",end);
    return rc || m || g || !muted || u || stop || end;
}
int main(int argc,char **argv)
{
    alarm(25); setbuf(stdout,0); setbuf(stderr,0);
    void *lib=dlopen("/vendor/lib64/libaudio_primary_impl_vendor.z.so",RTLD_NOW|RTLD_LOCAL);
    if (!lib) { printf("AUDIO_VDI_LOAD_ERROR=%s\n",dlerror()); return 2; }
    struct hdi_manager *(*create)(void)=dlsym(lib,"AudioManagerCreateIfInstance");
    int (*destroy)(struct hdi_manager *)=dlsym(lib,"AudioManagerDestroyIfInstance");
    if (!create || !destroy) return 2;
    void (*proxy_release)(const char *,struct hdi_manager *,bool)=0;
    struct hdi_manager *m=0;
    if (argc>1 && (!strcmp(argv[1],"proxy") || !strcmp(argv[1],"auto"))) {
        int automatic=!strcmp(argv[1],"auto");
        void *proxy=dlopen(automatic?"libaudio_proxy_6.0.z.so":"libaudio_proxy_6.1.z.so",RTLD_NOW|RTLD_GLOBAL);
        if (!proxy) { printf("AUDIO_PROXY_LOAD_ERROR=%s\n",dlerror()); return 2; }
        struct hdi_manager *(*get)(const char *,bool)=dlsym(automatic?RTLD_DEFAULT:proxy,
            automatic?"IAudioManagerGetInstance":"IAudioManagerGetInstanceV6_1");
        proxy_release=dlsym(automatic?RTLD_DEFAULT:proxy,
            automatic?"IAudioManagerReleaseInstance":"IAudioManagerReleaseInstanceV6_1");
        if (!get || !proxy_release) return 2;
        m=get("audio_manager_service",!automatic);
        printf("AUDIO_PROXY_DIRECT_MANAGER=%p\n",(void *)m);
    } else m=create();
    printf("AUDIO_VDI_MANAGER=%p\n",(void *)m);
    if (!m) return 2;
    struct AudioAdapterDescriptorVdi descs[20]={0}; uint32_t count=20;
    int rc=m->GetAllAdapters(m,descs,&count);
    printf("AUDIO_VDI_GET_ADAPTERS rc=%d count=%u\n",rc,count);
    struct hdi_adapter *a=0;
    if (!rc && count==1 && descs[0].adapterName) {
        printf("AUDIO_VDI_ADAPTER name=%s ports=%u\n",descs[0].adapterName,descs[0].portsLen);
        rc=m->LoadAdapter(m,&descs[0],&a);
        printf("AUDIO_VDI_LOAD_ADAPTER rc=%d adapter=%p\n",rc,(void *)a);
        if (!rc && a) {
            rc=a->InitAllPorts(a); printf("AUDIO_VDI_INIT_PORTS_RC=%d\n",rc);
            if (!rc) rc=one_stream(lib,a,2);
            if (!rc) rc=one_stream(lib,a,4);
            int end=m->UnloadAdapter(m,"primary"); printf("AUDIO_VDI_UNLOAD_RC=%d\n",end);
            if (!rc) rc=end;
        }
    } else rc=3;
    int end=0;
    if (proxy_release) proxy_release("audio_manager_service",m,true);
    else end=destroy(m);
    printf("AUDIO_VDI_RELEASE_RC=%d\n",end);
    for (unsigned i=0;i<count && i<20;i++) {
        for (unsigned j=0;j<descs[i].portsLen;j++) free(descs[i].ports[j].portName);
        free(descs[i].ports); free(descs[i].adapterName);
    }
    printf("AUDIO_VDI_CHECK_EXIT=%d\n",rc || end);
    return rc || end;
}
