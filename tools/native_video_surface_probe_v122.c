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
#include <native_image/native_image.h>
#include <native_window/external_window.h>
#include <native_buffer/native_buffer.h>
#include <poll.h>

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

API(OH_ConsumerSurface_Create);
API(OH_NativeImage_AcquireNativeWindow);
API(OH_NativeImage_AcquireNativeWindowBuffer);
API(OH_NativeImage_ReleaseNativeWindowBuffer);
API(OH_NativeImage_Destroy);
API(OH_NativeWindow_GetBufferHandleFromNative);
API(OH_NativeWindow_NativeObjectReference);
API(OH_NativeWindow_NativeObjectUnreference);
API(OH_NativeBuffer_FromNativeWindowBuffer);
API(OH_NativeBuffer_Map);
API(OH_NativeBuffer_Unmap);
API(OH_VideoDecoder_SetSurface);
API(OH_VideoDecoder_RenderOutputBuffer);

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
    printf("OUTPUT index=%u bytes=%d pts=%" PRId64 " flags=%u attr_result=%d\n",
           index, a.size, a.pts, a.flags, r);
    if (r) atomic_store(&s->failed, 1);
    if (!(a.flags & AVCODEC_BUFFER_FLAGS_EOS)) {
        atomic_fetch_add(&s->frames, 1);
        r = p_OH_VideoDecoder_RenderOutputBuffer(c, index);
    } else {
        r = p_OH_VideoDecoder_FreeOutputBuffer(c, index);
    }
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
    const char *libs[] = {"libnative_media_core.so", "libnative_media_codecbase.so", "libnative_media_vdec.so", "libnative_image.so", "libnative_window.so", "libnative_buffer.so"};
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
    LOAD(OH_ConsumerSurface_Create); LOAD(OH_NativeImage_AcquireNativeWindow);
    LOAD(OH_NativeImage_AcquireNativeWindowBuffer); LOAD(OH_NativeImage_ReleaseNativeWindowBuffer);
    LOAD(OH_NativeImage_Destroy); LOAD(OH_NativeWindow_GetBufferHandleFromNative);
    LOAD(OH_NativeWindow_NativeObjectReference); LOAD(OH_NativeWindow_NativeObjectUnreference);
    LOAD(OH_NativeBuffer_FromNativeWindowBuffer); LOAD(OH_NativeBuffer_Map); LOAD(OH_NativeBuffer_Unmap);
    LOAD(OH_VideoDecoder_SetSurface); LOAD(OH_VideoDecoder_RenderOutputBuffer);
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
    OH_NativeImage *image = p_OH_ConsumerSurface_Create();
    OHNativeWindow *window = image ? p_OH_NativeImage_AcquireNativeWindow(image) : NULL;
    printf("CONSUMER image=%p window=%p\n", (void *)image, (void *)window);
    if (!window) return 11;
    OH_AVCodecCallback cb = {error_cb, stream_cb, input_cb, output_cb};
    int r = p_OH_VideoDecoder_RegisterCallback(codec, cb, &s);
    OH_AVFormat *format = p_OH_AVFormat_CreateVideoFormat(mime, 64, 64);
    if (!format) return 8;
    const char **key = dlsym(RTLD_DEFAULT, "OH_MD_KEY_PIXEL_FORMAT");
    if (!key || !p_OH_AVFormat_SetIntValue(format, *key, 2)) return 9;
    printf("REGISTER_CALLBACK=%d\n", r);
    if (!r) { r = p_OH_VideoDecoder_Configure(codec, format); printf("CONFIGURE=%d\n",r); }
    if (!r) { r = p_OH_VideoDecoder_SetSurface(codec, window); printf("SET_SURFACE=%d\n", r); }
    p_OH_AVFormat_Destroy(format);
    if (!r) { r = p_OH_VideoDecoder_Prepare(codec); printf("PREPARE=%d\n",r); }
    if (!r) { r = p_OH_VideoDecoder_Start(codec); printf("START=%d\n",r); }
    int consumed = 0;
    if (!r) {
        for (int i = 0; i < 250 && !atomic_load(&s.failed) && (!atomic_load(&s.eos) || consumed < atomic_load(&s.frames)); ++i) {
            OHNativeWindowBuffer *buffer = NULL;
            int fence = -1;
            int acquire = p_OH_NativeImage_AcquireNativeWindowBuffer(image, &buffer, &fence);
            if (acquire) { usleep(100000); continue; }
            p_OH_NativeWindow_NativeObjectReference(buffer);
            if (fence >= 0) {
                struct pollfd pfd = {.fd = fence, .events = POLLIN};
                if (poll(&pfd, 1, 1000) <= 0) atomic_store(&s.failed, 1);
                close(fence);
            }
            BufferHandle *h = p_OH_NativeWindow_GetBufferHandleFromNative(buffer);
            OH_NativeBuffer *nb = NULL;
            void *addr = NULL;
            int mapped = p_OH_NativeBuffer_FromNativeWindowBuffer(buffer, &nb);
            if (!mapped) mapped = p_OH_NativeBuffer_Map(nb, &addr);
            uint32_t hash = 2166136261u;
            if (!mapped && addr && h && h->width == 64 && h->height == 64 &&
                h->stride >= 64 && h->size >= h->stride * 96 && (h->format == 24 || h->format == 25)) {
                for (int y = 0; y < 96; ++y) {
                    uint8_t *row = (uint8_t *)addr + y * h->stride;
                    for (int x = 0; x < 64; ++x) hash = (hash ^ row[x]) * 16777619u;
                    if (fwrite(row, 1, 64, s.out) != 64) atomic_store(&s.failed, 1);
                }
            } else atomic_store(&s.failed, 1);
            if (!mapped) p_OH_NativeBuffer_Unmap(nb);
            printf("SURFACE frame=%d map=%d size=%d stride=%d height=%d format=%d fnv32=%08x\n",
                consumed, mapped, h ? h->size : -1, h ? h->stride : -1,
                h ? h->height : -1, h ? h->format : -1, hash);
            int release = p_OH_NativeImage_ReleaseNativeWindowBuffer(image, buffer, -1);
            p_OH_NativeWindow_NativeObjectUnreference(buffer);
            if (release) atomic_store(&s.failed, 1);
            ++consumed;
        }
        r = !atomic_load(&s.eos) || atomic_load(&s.failed) || atomic_load(&s.frames) != 12 || consumed != 12;
    }
    int stop = p_OH_VideoDecoder_Stop(codec);
    int destroy = p_OH_VideoDecoder_Destroy(codec);
    p_OH_NativeImage_Destroy(&image);
    fclose(s.in); fclose(s.out);
    printf("SURFACE_CONSUMED=%d\n", consumed);
    printf("DECODE_RESULT=%s fed=%u frames=%d eos=%d failed=%d stop=%d destroy=%d\n",!r && !stop && !destroy ? "PASS":"FAIL",s.fed,atomic_load(&s.frames),atomic_load(&s.eos),atomic_load(&s.failed),stop,destroy);
    return r || stop || destroy ? 10 : 0;
}
