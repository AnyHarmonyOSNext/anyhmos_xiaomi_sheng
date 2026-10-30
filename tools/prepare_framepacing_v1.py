"""Create a reviewable hardware-vsync variant, preserving v87 sources."""
from pathlib import Path

r=Path(__file__).resolve().parent.parent
d=r/'compat/sheng-graphics/framepacing-v1'
d.mkdir(exist_ok=True)
s=(r/'compat/sheng-graphics/brightness-v2/composer_vdi.cpp').read_text(encoding='utf-8')
s=s.replace('uint32_t selectedMode = 0;', 'uint32_t selectedMode = 0, hardwareCrtcIndex = 0;')
s=s.replace('    clientCrop = {0, 0, mode.hdisplay, mode.vdisplay};\n    Ace5Log(',
'''    hardwareCrtcIndex = crtcIndex;
    uint64_t monotonic = 0;
    if (drmGetCap(drm, DRM_CAP_TIMESTAMP_MONOTONIC, &monotonic) || !monotonic) {
        Log("hardware vsync requires monotonic kernel timestamps"); CleanupDrm(); return FAIL;
    }
    clientCrop = {0, 0, mode.hdisplay, mode.vdisplay};
    Ace5Log(''')
start=s.index('void *VsyncLoop(void *)')
end=s.index('uint32_t Format(',start)
s=s[:start]+'''void *VsyncLoop(void *)
{
    unsigned sequence = 0, errors = 0;
    for (;;) {
        bool enabled;
        {
            std::lock_guard<std::mutex> state(vsyncMutex);
            if (quit) break;
            enabled = vsyncEnabled;
        }
        if (!enabled) { usleep(5000); continue; }
        // Only the vblank worker waits here: never hold the commit mutex.
        // Timestamp is the kernel's actual scanout timestamp, not wake time.
        drmVBlank wait{};
        wait.request.type = static_cast<drmVBlankSeqType>(DRM_VBLANK_RELATIVE |
            (hardwareCrtcIndex << DRM_VBLANK_HIGH_CRTC_SHIFT));
        wait.request.sequence = 1;
        int rc;
        do { rc = drmWaitVBlank(drm, &wait); } while (rc < 0 && errno == EINTR);
        if (rc) {
            if (++errors <= 4) Ace5Log("hardware vsync wait failed errno=%d", errno);
            usleep(20000); continue;
        }
        errors = 0;
        uint64_t timestamp = uint64_t(wait.reply.tval_sec) * 1000000000ULL +
            uint64_t(wait.reply.tval_usec) * 1000ULL;
        VBlankCallback callback; void *data;
        {
            std::lock_guard<std::mutex> state(vsyncMutex);
            if (quit) break;
            callback = vsyncEnabled ? vsyncCallback : nullptr; data = vsyncData;
        }
        if (callback) callback(++sequence, timestamp, data);
    }
    return nullptr;
}
''' +s[end:]
assert 'clock_nanosleep' not in s
(d/'composer_vdi.cpp').write_text(s,encoding='utf-8',newline='\n')
print('hardware vblank backend staged, still fixed120, blocking commits unchanged')
