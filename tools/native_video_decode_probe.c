/* Bounded real donor NDK decode test. No service or codec return is mocked. */
#define _GNU_SOURCE
#include <multimedia/player_framework/native_avcodec_videodecoder.h>
#include <multimedia/player_framework/native_avcapability.h>
#include <dlfcn.h>
#include <stdatomic.h>
#include <pthread.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>
#include <inttypes.h>

#define API(name) static __typeof__(&name) p_##name
API(OH_AVCodec_GetCapabilityByCategory);
API(OH_AVCapability_GetName);
API(OH_VideoDecoder_CreateByName);
API(OH_VideoDecoder_RegisterCallback);
API(OH_VideoDecoder_Configure);
API(OH_VideoDecoder_Prepare);
API(OH_VideoDecoder_Start);
API(OH_VideoDecoder_Stop);
API(OH_VideoDecoder_Destroy);
API(OH_VideoDecoder_PushInputBuffer);
API(OH_VideoDecoder_FreeOutputBuffer);
API(OH_AVBuffer_GetAddr);
API(OH_AVBuffer_GetCapacity);
API(OH_AVBuffer_GetBufferAttr);
API(OH_AVBuffer_SetBufferAttr);
API(OH_AVFormat_CreateVideoFormat);
API(OH_AVFormat_SetIntValue);
API(OH_AVFormat_GetIntValue);
API(OH_AVFormat_Destroy);

struct state {
    FILE *in, *out;
    pthread_mutex_t mutex;
    atomic_int failed, eos, frames;
    unsigned fed;
    int sent_eos;
};
static void error_cb(OH_AVCodec *c, int32_t e, void *user)
{
    (void)c;
    struct state *s = user;
    printf("DECODE_ERROR=%d\n", e);
    atomic_store(&s->failed, 1);
}
static void stream_cb(OH_AVCodec *c, OH_AVFormat *f, void *user)
{
    (void)c; (void)user;
    const char *keys[] = {"width", "height", "stride", "slice_height", "pixel_format"};
    for (unsigned i = 0; i < sizeof(keys)/sizeof(keys[0]); ++i) {
        int32_t v = -1;
        if (p_OH_AVFormat_GetIntValue(f, keys[i], &v))
            printf("OUTPUT_FORMAT %s=%d\n", keys[i], v);
    }
}
static void input_cb(OH_AVCodec *c, uint32_t index, OH_AVBuffer *b, void *user)
{
    struct state *s = user;
    OH_AVCodecBufferAttr a = {0};
    pthread_mutex_lock(&s->mutex);
    if (s->sent_eos || atomic_load(&s->failed)) {
        pthread_mutex_unlock(&s->mutex);
        return;
    }
    uint32_t n = 0;
    size_t got = fread(&n, 1, sizeof(n), s->in);
    if (!got && feof(s->in)) {
        a.flags = AVCODEC_BUFFER_FLAGS_EOS;
        a.pts = (int64_t)s->fed * 33333;
        s->sent_eos = 1;
    } else if (got != sizeof(n) || n == 0 || n > 1048576 ||
               (int32_t)n > p_OH_AVBuffer_GetCapacity(b) ||
               !p_OH_AVBuffer_GetAddr(b) ||
               fread(p_OH_AVBuffer_GetAddr(b), 1, n, s->in) != n) {
        puts("INVALID_TEST_PACKET_OR_INPUT_BUFFER=1");
        atomic_store(&s->failed, 1);
        pthread_mutex_unlock(&s->mutex);
        return;
    } else {
        a.pts = (int64_t)s->fed * 33333;
        a.size = (int32_t)n;
        a.flags = s->fed == 0 ? AVCODEC_BUFFER_FLAGS_SYNC_FRAME : AVCODEC_BUFFER_FLAGS_NONE;
        ++s->fed;
    }
    pthread_mutex_unlock(&s->mutex);
    int r = p_OH_AVBuffer_SetBufferAttr(b, &a);
    if (!r) r = p_OH_VideoDecoder_PushInputBuffer(c, index);
    printf("INPUT index=%u bytes=%d pts=%" PRId64 " flags=%u result=%d\n", index,a.size,a.pts,a.flags,r);
    if (r) atomic_store(&s->failed, 1);
}
static void output_cb(OH_AVCodec *c, uint32_t index, OH_AVBuffer *b, void *user)
{
    struct state *s = user;
    OH_AVCodecBufferAttr a = {0};
    int r = p_OH_AVBuffer_GetBufferAttr(b, &a);
    int cap = p_OH_AVBuffer_GetCapacity(b);
    uint8_t *p = p_OH_AVBuffer_GetAddr(b);
    uint32_t hash = 2166136261u;
    /* The donor HEVC EOS marker can retain stale bytes/PTS from an old output
       buffer. EOS is control only; count and write the twelve preceding frames. */
    if (!r && !(a.flags & AVCODEC_BUFFER_FLAGS_EOS) && a.size > 0 && p && a.offset >= 0 && a.offset <= cap && a.size <= cap-a.offset) {
        for (int i = 0; i < a.size; ++i) hash = (hash ^ p[a.offset+i]) * 16777619u;
        if (fwrite(p+a.offset, 1, (size_t)a.size, s->out) != (size_t)a.size)
            atomic_store(&s->failed, 1);
        atomic_fetch_add(&s->frames, 1);
    } else if (r || a.size < 0 || (a.size && (!p || a.offset < 0 || a.offset > cap || a.size > cap-a.offset))) {
        atomic_store(&s->failed, 1);
    }
    printf("OUTPUT index=%u bytes=%d capacity=%d pts=%" PRId64 " flags=%u fnv32=%08x attr_result=%d\n",index,a.size,cap,a.pts,a.flags,hash,r);
    r = p_OH_VideoDecoder_FreeOutputBuffer(c, index);
    if (r) atomic_store(&s->failed, 1);
    if (a.flags & AVCODEC_BUFFER_FLAGS_EOS) atomic_store(&s->eos, 1);
}
int main(int argc, char **argv)
{
    if (argc != 3 && argc != 4) return 2;
    const char *mime = argc == 4 ? argv[3] : "video/avc";
    if (strcmp(mime, "video/avc") && strcmp(mime, "video/hevc")) return 2;
    setvbuf(stdout, NULL, _IOLBF, 0);
    alarm(35);
    const char *libs[] = {"libnative_media_core.so", "libnative_media_codecbase.so", "libnative_media_vdec.so"};
    for (unsigned i = 0; i < sizeof(libs)/sizeof(libs[0]); ++i) {
        if (!dlopen(libs[i], RTLD_NOW|RTLD_GLOBAL)) {
            printf("DLOPEN_FAILED %s %s\n", libs[i], dlerror());
            return 3;
        }
    }
#define LOAD(name) do { p_##name = dlsym(RTLD_DEFAULT, #name); if (!p_##name) { puts("MISSING_SYMBOL=" #name); return 4; } } while (0)
    LOAD(OH_AVCodec_GetCapabilityByCategory); LOAD(OH_AVCapability_GetName);
    LOAD(OH_VideoDecoder_CreateByName); LOAD(OH_VideoDecoder_RegisterCallback);
    LOAD(OH_VideoDecoder_Configure); LOAD(OH_VideoDecoder_Prepare);
    LOAD(OH_VideoDecoder_Start); LOAD(OH_VideoDecoder_Stop); LOAD(OH_VideoDecoder_Destroy);
    LOAD(OH_VideoDecoder_PushInputBuffer); LOAD(OH_VideoDecoder_FreeOutputBuffer);
    LOAD(OH_AVBuffer_GetAddr); LOAD(OH_AVBuffer_GetCapacity);
    LOAD(OH_AVBuffer_GetBufferAttr); LOAD(OH_AVBuffer_SetBufferAttr);
    LOAD(OH_AVFormat_CreateVideoFormat); LOAD(OH_AVFormat_SetIntValue);
    LOAD(OH_AVFormat_GetIntValue); LOAD(OH_AVFormat_Destroy);
    const char *mimes[] = {"video/avc", "video/hevc", "video/mp4v-es", "video/x-vnd.on2.vp9"};
    for (unsigned i = 0; i < sizeof(mimes)/sizeof(mimes[0]); ++i) {
        for (int cat = 0; cat <= 1; ++cat) {
            OH_AVCapability *cap = p_OH_AVCodec_GetCapabilityByCategory(mimes[i], false, (OH_AVCodecCategory)cat);
            printf("CAPABILITY mime=%s category=%s name=%s\n", mimes[i],cat ? "software":"hardware",cap ? p_OH_AVCapability_GetName(cap):"unavailable");
        }
    }
    OH_AVCapability *cap = p_OH_AVCodec_GetCapabilityByCategory(mime, false, SOFTWARE);
    if (!cap) return 5;
    const char *name = p_OH_AVCapability_GetName(cap);
    OH_AVCodec *codec = name ? p_OH_VideoDecoder_CreateByName(name) : NULL;
    printf("SOFTWARE_DECODER mime=%s name=%s instance=%p\n", mime, name ? name:"null", (void *)codec);
    if (!codec) return 6;
    struct state s = {.mutex = PTHREAD_MUTEX_INITIALIZER};
    s.in = fopen(argv[1], "rb"); s.out = fopen(argv[2], "wb");
    if (!s.in || !s.out) return 7;
    OH_AVCodecCallback cb = {error_cb, stream_cb, input_cb, output_cb};
    int r = p_OH_VideoDecoder_RegisterCallback(codec, cb, &s);
    OH_AVFormat *format = p_OH_AVFormat_CreateVideoFormat(mime, 64, 64);
    if (!format) return 8;
    const char **key = dlsym(RTLD_DEFAULT, "OH_MD_KEY_PIXEL_FORMAT");
    if (!key || !p_OH_AVFormat_SetIntValue(format, *key, 2)) return 9;
    printf("REGISTER_CALLBACK=%d\n", r);
    if (!r) { r = p_OH_VideoDecoder_Configure(codec, format); printf("CONFIGURE=%d\n",r); }
    p_OH_AVFormat_Destroy(format);
    if (!r) { r = p_OH_VideoDecoder_Prepare(codec); printf("PREPARE=%d\n",r); }
    if (!r) { r = p_OH_VideoDecoder_Start(codec); printf("START=%d\n",r); }
    if (!r) {
        for (int i = 0; i < 250 && !atomic_load(&s.failed) && !atomic_load(&s.eos); ++i) usleep(100000);
        r = !atomic_load(&s.eos) || atomic_load(&s.failed) || atomic_load(&s.frames) != 12;
    }
    int stop = p_OH_VideoDecoder_Stop(codec);
    int destroy = p_OH_VideoDecoder_Destroy(codec);
    fclose(s.in); fclose(s.out);
    printf("DECODE_RESULT=%s fed=%u frames=%d eos=%d failed=%d stop=%d destroy=%d\n",!r && !stop && !destroy ? "PASS":"FAIL",s.fed,atomic_load(&s.frames),atomic_load(&s.eos),atomic_load(&s.failed),stop,destroy);
    return r || stop || destroy ? 10 : 0;
}
