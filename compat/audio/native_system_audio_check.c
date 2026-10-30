/* SPDX-License-Identifier: MIT - exercise the original public OH audio API. */
#include <ohaudio/native_audiostreambuilder.h>
#include <ohaudio/native_audiorenderer.h>
#include <stdio.h>
#include <stdint.h>
#include <math.h>
#include <unistd.h>

static uint64_t submitted,callbacks;
static int32_t write_data(OH_AudioRenderer *r,void *user,void *buffer,int32_t length)
{
    (void)r; (void)user;
    int16_t *out=buffer;
    uint64_t start=__atomic_load_n(&submitted,__ATOMIC_RELAXED);
    for (int32_t i=0;i<length/4;i++) {
        uint64_t f=start+(unsigned)i;
        bool tone=(f<7200 || (f>=14400 && f<21600));
        int16_t value=tone?(int16_t)(400.0*sin(6.283185307179586*660.0*f/48000.0)):0;
        out[2*i]=out[2*i+1]=value;
    }
    __atomic_fetch_add(&submitted,(uint64_t)length/4,__ATOMIC_RELAXED);
    __atomic_fetch_add(&callbacks,1,__ATOMIC_RELAXED);
    return 0;
}
#define CHECK(call) do { int rc=(call); printf("SYSTEM_AUDIO_%s_RC=%d\n",#call,rc); if(rc) { result=rc; goto cleanup; } } while(0)
int main(void)
{
    setbuf(stdout,0); alarm(10);
    OH_AudioStreamBuilder *b=0; OH_AudioRenderer *r=0; int result=0;
    OH_AudioRenderer_Callbacks cb={.OH_AudioRenderer_OnWriteData=write_data};
    CHECK(OH_AudioStreamBuilder_Create(&b,AUDIOSTREAM_TYPE_RENDERER));
    CHECK(OH_AudioStreamBuilder_SetSamplingRate(b,48000));
    CHECK(OH_AudioStreamBuilder_SetChannelCount(b,2));
    CHECK(OH_AudioStreamBuilder_SetSampleFormat(b,AUDIOSTREAM_SAMPLE_S16LE));
    CHECK(OH_AudioStreamBuilder_SetLatencyMode(b,AUDIOSTREAM_LATENCY_MODE_NORMAL));
    CHECK(OH_AudioStreamBuilder_SetRendererInfo(b,AUDIOSTREAM_USAGE_MUSIC));
    CHECK(OH_AudioStreamBuilder_SetRendererCallback(b,cb,0));
    CHECK(OH_AudioStreamBuilder_GenerateRenderer(b,&r));
    CHECK(OH_AudioRenderer_SetVolume(r,0.1f));
    CHECK(OH_AudioRenderer_Start(r));
    usleep(1400000);
    int64_t frames=0;
    CHECK(OH_AudioRenderer_GetFramesWritten(r,&frames));
    printf("SYSTEM_AUDIO_RENDERED callbacks=%llu submitted_frames=%llu framework_frames=%lld\n",
        (unsigned long long)__atomic_load_n(&callbacks,__ATOMIC_RELAXED),
        (unsigned long long)__atomic_load_n(&submitted,__ATOMIC_RELAXED),(long long)frames);
    CHECK(OH_AudioRenderer_Stop(r));
    if (!callbacks || frames<=0) result=9;
cleanup:
    if (r) { int rc=OH_AudioRenderer_Release(r); printf("SYSTEM_AUDIO_RELEASE_RC=%d\n",rc); if (rc) result=rc; }
    if (b) { int rc=OH_AudioStreamBuilder_Destroy(b); printf("SYSTEM_AUDIO_BUILDER_DESTROY_RC=%d\n",rc); if (rc) result=rc; }
    printf("SYSTEM_AUDIO_CHECK_EXIT=%d\n",result); return result?1:0;
}
