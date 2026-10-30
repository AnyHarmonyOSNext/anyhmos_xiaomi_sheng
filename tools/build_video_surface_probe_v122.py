"""Build a bounded independent Surface consumer test from the buffer probe."""
from pathlib import Path
import subprocess

r = Path(__file__).resolve().parent.parent
s = (r / 'tools/native_video_decode_probe.c').read_text()
def replace(old, new):
    global s
    assert s.count(old) == 1, old[:100]
    s = s.replace(old, new)

replace('#include <inttypes.h>', '''#include <inttypes.h>
#include <native_image/native_image.h>
#include <native_window/external_window.h>
#include <native_buffer/native_buffer.h>
#include <poll.h>''')
replace('struct state {', '''API(OH_ConsumerSurface_Create);
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

struct state {''')
start = s.index('    int cap = p_OH_AVBuffer_GetCapacity(b);', s.index('static void output_cb'))
end = s.index('\n    if (r) atomic_store', start)
s = s[:start] + '''    printf("OUTPUT index=%u bytes=%d pts=%" PRId64 " flags=%u attr_result=%d\\n",
           index, a.size, a.pts, a.flags, r);
    if (r) atomic_store(&s->failed, 1);
    if (!(a.flags & AVCODEC_BUFFER_FLAGS_EOS)) {
        atomic_fetch_add(&s->frames, 1);
        r = p_OH_VideoDecoder_RenderOutputBuffer(c, index);
    } else {
        r = p_OH_VideoDecoder_FreeOutputBuffer(c, index);
    }''' + s[end:]
replace('"libnative_media_vdec.so"}', '"libnative_media_vdec.so", "libnative_image.so", "libnative_window.so", "libnative_buffer.so"}')
replace('    const char *mimes[]', '''    LOAD(OH_ConsumerSurface_Create); LOAD(OH_NativeImage_AcquireNativeWindow);
    LOAD(OH_NativeImage_AcquireNativeWindowBuffer); LOAD(OH_NativeImage_ReleaseNativeWindowBuffer);
    LOAD(OH_NativeImage_Destroy); LOAD(OH_NativeWindow_GetBufferHandleFromNative);
    LOAD(OH_NativeWindow_NativeObjectReference); LOAD(OH_NativeWindow_NativeObjectUnreference);
    LOAD(OH_NativeBuffer_FromNativeWindowBuffer); LOAD(OH_NativeBuffer_Map); LOAD(OH_NativeBuffer_Unmap);
    LOAD(OH_VideoDecoder_SetSurface); LOAD(OH_VideoDecoder_RenderOutputBuffer);
    const char *mimes[]''')
replace('    OH_AVCodecCallback cb =', '''    OH_NativeImage *image = p_OH_ConsumerSurface_Create();
    OHNativeWindow *window = image ? p_OH_NativeImage_AcquireNativeWindow(image) : NULL;
    printf("CONSUMER image=%p window=%p\\n", (void *)image, (void *)window);
    if (!window) return 11;
    OH_AVCodecCallback cb =''')
replace('    p_OH_AVFormat_Destroy(format);', '''    if (!r) { r = p_OH_VideoDecoder_SetSurface(codec, window); printf("SET_SURFACE=%d\\n", r); }
    p_OH_AVFormat_Destroy(format);''')
replace('    if (!r) {\n        for (int i = 0; i < 250', '    int consumed = 0;\n    if (!r) {\n        for (int i = 0; i < 250')
replace(' && !atomic_load(&s.eos); ++i) usleep(100000);', ''' && (!atomic_load(&s.eos) || consumed < atomic_load(&s.frames)); ++i) {
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
            printf("SURFACE frame=%d map=%d size=%d stride=%d height=%d format=%d fnv32=%08x\\n",
                consumed, mapped, h ? h->size : -1, h ? h->stride : -1,
                h ? h->height : -1, h ? h->format : -1, hash);
            int release = p_OH_NativeImage_ReleaseNativeWindowBuffer(image, buffer, -1);
            p_OH_NativeWindow_NativeObjectUnreference(buffer);
            if (release) atomic_store(&s.failed, 1);
            ++consumed;
        }''')
replace('atomic_load(&s.frames) != 12;', 'atomic_load(&s.frames) != 12 || consumed != 12;')
replace('    fclose(s.in); fclose(s.out);', '    p_OH_NativeImage_Destroy(&image);\n    fclose(s.in); fclose(s.out);\n    printf("SURFACE_CONSUMED=%d\\n", consumed);')
out = r / 'compat/debug-tools/native_video_surface_probe_v122'
src = r / 'tools/native_video_surface_probe_v122.c'
src.write_text(s)
sdk = Path('/root/hmos-work/sdk-6.0.0.47/installed/native')
subprocess.run([str(sdk/'llvm/bin/clang'), '--target=aarch64-linux-ohos', '-O2', '-std=gnu11', '-Wall', '-Wextra', '-Werror', str(src), '-o', str(out)], check=True)
subprocess.run([str(sdk/'llvm/bin/llvm-strip'), str(out)], check=True)
print(out, out.stat().st_size)
