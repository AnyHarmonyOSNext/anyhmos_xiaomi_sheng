#include <fcntl.h>
#include <stdint.h>
#include <stdio.h>
#include <unistd.h>
#include <xf86drm.h>
#include <xf86drmMode.h>

int main(void)
{
    alarm(15);
    int fd = open("/dev/dri/card0", O_RDWR | O_CLOEXEC);
    if (fd < 0) return 2;
    drmModeRes *resources = drmModeGetResources(fd);
    if (!resources) return 3;
    unsigned index = 0;
    int found = 0;
    for (int i = 0; i < resources->count_crtcs; ++i) {
        drmModeCrtc *crtc = drmModeGetCrtc(fd, resources->crtcs[i]);
        if (crtc && crtc->mode_valid) {
            index = i; found = 1;
            printf("SCANOUT_MODE %ux%u@%u crtc=%u\n", crtc->mode.hdisplay,
                crtc->mode.vdisplay, crtc->mode.vrefresh, crtc->crtc_id);
        }
        drmModeFreeCrtc(crtc);
        if (found) break;
    }
    drmModeFreeResources(resources);
    if (!found) return 4;
    uint64_t previous = 0, sum = 0, minimum = UINT64_MAX, maximum = 0;
    // 只读采样内核 VBlank 时间戳，不请求显示主控或修改模式
    for (unsigned i = 0; i <= 240; ++i) {
        drmVBlank event = {0};
        event.request.type = DRM_VBLANK_RELATIVE | (index << DRM_VBLANK_HIGH_CRTC_SHIFT);
        event.request.sequence = 1;
        if (drmWaitVBlank(fd, &event)) return 5;
        uint64_t timestamp = (uint64_t)event.reply.tval_sec * 1000000000ULL +
            (uint64_t)event.reply.tval_usec * 1000ULL;
        if (i) {
            if (timestamp <= previous) return 6;
            uint64_t delta = timestamp - previous;
            sum += delta;
            if (delta < minimum) minimum = delta;
            if (delta > maximum) maximum = delta;
        }
        previous = timestamp;
    }
    printf("VBLANK_SAMPLES=240 avg_ns=%llu min_ns=%llu max_ns=%llu\n",
        (unsigned long long)(sum / 240), (unsigned long long)minimum, (unsigned long long)maximum);
    close(fd);
    return 0;
}
