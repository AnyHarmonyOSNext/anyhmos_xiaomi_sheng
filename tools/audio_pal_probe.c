/* Bounded original303 PAL diagnostics. Playback requires explicit silence/tone mode.
 * Run after the loader has finished constructors: PAL creates threads which
 * may call dlopen/dlsym, and must not be joined while a constructor owns the
 * dynamic linker's lock.
 */
#include <PalDefs.h>
#include <stddef.h>
typedef unsigned long size_t;
typedef long ssize_t;
extern void *dlopen(const char *, int);
extern void *dlsym(void *, const char *);
extern char *dlerror(void);
extern char *getenv(const char *);
extern int strcmp(const char *, const char *);
extern int snprintf(char *, size_t, const char *, ...);
extern int vsnprintf(char *, size_t, const char *, __builtin_va_list);
extern ssize_t write(int, const void *, size_t);
extern void _exit(int);

int __android_log_print(int priority, const char *tag, const char *fmt, ...)
{
    static unsigned count;
    if (count++ >= 1200) return 0;
    char b[768];
    int n = snprintf(b, sizeof(b), "PAL_LOG_%d_%s: ", priority, tag ? tag : "?");
    if (n < 0 || n >= (int)sizeof(b)) return 0;
    __builtin_va_list ap;
    __builtin_va_start(ap, fmt);
    int m = vsnprintf(b+n, sizeof(b)-(size_t)n, fmt, ap);
    __builtin_va_end(ap);
    if (m < 0) return 0;
    size_t used = (size_t)n+(size_t)m;
    if (used >= sizeof(b)-2) used = sizeof(b)-2;
    b[used++] = '\n';
    (void)write(1, b, used);
    return m;
}

static void say(const char *label, int value)
{
    char b[100];
    int n = snprintf(b, sizeof(b), "%s=%d\n", label, value);
    if (n > 0 && n < (int)sizeof(b)) (void)write(1, b, (size_t)n);
}

static int open_stream(void *h, int test_audio)
{
    int (*open_fn)(struct pal_stream_attributes *, unsigned, struct pal_device *,
                   unsigned, struct modifier_kv *, pal_stream_callback, unsigned long,
                   pal_stream_handle_t **) = dlsym(h, "pal_stream_open");
    int (*close_fn)(pal_stream_handle_t *)=dlsym(h, "pal_stream_close");
    int (*volume_fn)(pal_stream_handle_t *, struct pal_volume_data *)=dlsym(h, "pal_stream_set_volume");
    int (*getbuf_fn)(pal_stream_handle_t *, pal_buffer_config_t *, pal_buffer_config_t *)=
        dlsym(h, "pal_stream_get_buffer_size");
    if (!open_fn || !close_fn || !volume_fn || !getbuf_fn) return -38;
    say("PAL_ABI_STREAM_ATTR_SIZE", sizeof(struct pal_stream_attributes));
    say("PAL_ABI_OUT_MEDIA_OFFSET", offsetof(struct pal_stream_attributes, out_media_config));
    say("PAL_ABI_DEVICE_SIZE", sizeof(struct pal_device));
    /* Stock private revisions may append fields to the public POD prefixes. */
    struct { struct pal_stream_attributes value; unsigned char tail[128]; } padded_attr={0};
    struct pal_stream_attributes *attr=&padded_attr.value;
    attr->type=PAL_STREAM_LOW_LATENCY;
    attr->direction=PAL_AUDIO_OUTPUT;
    attr->out_media_config.sample_rate=48000;
    attr->out_media_config.bit_width=16;
    attr->out_media_config.aud_fmt_id=PAL_AUDIO_FMT_PCM_S16_LE;
    attr->out_media_config.ch_info.channels=2;
    attr->out_media_config.ch_info.ch_map[0]=PAL_CHMAP_CHANNEL_FL;
    attr->out_media_config.ch_info.ch_map[1]=PAL_CHMAP_CHANNEL_FR;
    struct { struct pal_device value; unsigned char tail[128]; } padded_device={0};
    struct pal_device *device=&padded_device.value;
    device->id=PAL_DEVICE_OUT_SPEAKER;
    device->config=attr->out_media_config;
    pal_stream_handle_t *stream=0;
    int rc=open_fn(attr, 1, device, 0, 0, 0, 0, &stream);
    say("PAL_STREAM_OPEN_RC", rc);
    if (rc || !stream) return rc ? rc : -5;
    struct { unsigned count; struct pal_channel_vol_kv pair; } volume={1,{3,0.03f}};
    int vrc=volume_fn(stream, (struct pal_volume_data *)&volume);
    say("PAL_STREAM_VOLUME_RC", vrc);
    pal_buffer_config_t in={0}, out={0};
    int brc=getbuf_fn(stream, &in, &out);
    say("PAL_STREAM_GET_BUFFER_RC", brc);
    say("PAL_STREAM_OUT_BUFFER_SIZE", out.buf_size);
    say("PAL_STREAM_OUT_BUFFER_COUNT", out.buf_count);
    int src=0;
    if (test_audio && vrc == 0) {
        int (*setbuf_fn)(pal_stream_handle_t *, pal_buffer_config_t *, pal_buffer_config_t *)=
            dlsym(h, "pal_stream_set_buffer_size");
        int (*start_fn)(pal_stream_handle_t *)=dlsym(h, "pal_stream_start");
        int (*stop_fn)(pal_stream_handle_t *)=dlsym(h, "pal_stream_stop");
        int (*write_fn)(pal_stream_handle_t *, struct pal_buffer *)=dlsym(h, "pal_stream_write");
        if (!setbuf_fn || !start_fn || !stop_fn || !write_fn) src=-38;
        else {
            out.buf_count=2;
            out.buf_size=960;
            out.max_metadata_size=0;
            src=setbuf_fn(stream, 0, &out);
            say("PAL_STREAM_SET_BUFFER_RC", src);
            if (src == 0) {
                src=start_fn(stream);
                say("PAL_STREAM_START_RC", src);
                if (src == 0) {
                    short samples[480]={0};
                    struct { struct pal_buffer value; unsigned char tail[64]; } buffer={0};
                    buffer.value.buffer=(unsigned char *)samples;
                    buffer.value.size=sizeof(samples);
                    buffer.value.alloc_info.alloc_handle=-1;
                    unsigned written=0;
                    unsigned blocks=test_audio==2 ? 140 : 40;
                    for (unsigned i=0; i<blocks; i++) {
                        for (unsigned f=0; f<240; f++) {
                            int v=0;
                            if (test_audio==2 && (i<40 || (i>=80 && i<120))) {
                                unsigned local=(i%80)*240+f;
                                int phase=(int)(local%100);
                                v=(phase<25 ? phase : phase<75 ? 50-phase : phase-100)*82;
                                unsigned ramp=local<480 ? local : 9600-local<480 ? 9600-local : 480;
                                v=v*(int)ramp/480;
                            }
                            samples[2*f]=samples[2*f+1]=(short)v;
                        }
                        int w=write_fn(stream, &buffer.value);
                        if (w != (int)sizeof(samples)) { say("PAL_STREAM_SHORT_WRITE", w); src=w<0 ? w : -5; break; }
                        written+=(unsigned)w;
                    }
                    say(test_audio==2 ? "PAL_STREAM_TONE_BYTES" : "PAL_STREAM_SILENCE_BYTES", written);
                    int stoprc=stop_fn(stream);
                    say("PAL_STREAM_STOP_RC", stoprc);
                    if (!src) src=stoprc;
                }
            }
        }
    }
    int crc=close_fn(stream);
    say("PAL_STREAM_CLOSE_RC", crc);
    if (vrc) return vrc;
    /* -ENOSYS is an explicitly logged optional stock API; the supplied buffer
     * configuration and real write counts prove the streaming path instead. */
    if (brc && brc != -38) return brc;
    if (src) return src;
    return crc;
}

static void run(void)
{
    void *h = dlopen("libar-pal.so", 2);
    if (!h) {
        char b[500];
        int n = snprintf(b, sizeof(b), "PAL_DLOPEN_ERROR=%s\n", dlerror());
        if (n > 0 && n < (int)sizeof(b)) (void)write(1, b, (size_t)n);
        _exit(80);
    }
    say("PAL_DLOPEN", 1);
    char *mode = getenv("SHENG_PAL_PROBE_MODE");
    if (!mode || (strcmp(mode, "init") && strcmp(mode, "open") && strcmp(mode, "silence") && strcmp(mode, "tone"))) _exit(0);
    void *agm = dlopen("libagm.so", 2);
    if (!agm) _exit(83);
    int (*agm_init_fn)(void) = dlsym(agm, "agm_init");
    int (*agm_deinit_fn)(void) = dlsym(agm, "agm_deinit");
    if (!agm_init_fn || !agm_deinit_fn) _exit(84);
    int arc = agm_init_fn();
    say("PAL_AGM_INIT_RC", arc);
    if (arc != 0) _exit(85);
    int (*init)(void) = (int (*)(void))dlsym(h, "pal_init");
    void (*deinit)(void) = (void (*)(void))dlsym(h, "pal_deinit");
    if (getenv("SHENG_PAL_LIFECYCLE")) deinit = dlsym((void *)0, "pal_deinit");
    if (!init || !deinit) _exit(82);
    int rc = init();
    say("PAL_INIT_RC", rc);
    if (rc == 0) {
        if (strcmp(mode, "init"))
            rc=open_stream(h, !strcmp(mode, "tone") ? 2 : !strcmp(mode, "silence") ? 1 : 0);
        deinit();
        say("PAL_DEINIT_COMPLETED", 1);
    }
    say("PAL_AGM_DEINIT_RC", agm_deinit_fn());
    _exit(rc == 0 ? 0 : 81);
}

static int probe_main(int argc, char **argv, char **envp)
{
    (void)argc; (void)argv; (void)envp;
    run();
    return 0;
}

__attribute__((noreturn)) void __libc_init(void *raw_args, void (*onexit)(void),
    int (*original_main)(int, char **, char **), const void *structors)
{
    (void)original_main;
    void (*real)(void *, void (*)(void), int (*)(int, char **, char **), const void *) =
        dlsym((void *)-1L, "__libc_init");
    if (real) real(raw_args, onexit, probe_main, structors);
    _exit(90);
    __builtin_unreachable();
}
