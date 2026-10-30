"""Apply the verified two-plane sheng layout to the private adapter copy.

The reference checkout remains unchanged. No direct register programming.
"""
from pathlib import Path

workspace = Path('/mnt/c/SHENG_WORKSPACE')
source = Path('/root/hmos-work/graphics-deps/sheng-graphics-port/adapter/composer_vdi.cpp')
text = source.read_text()
if 'SHENG_SPLIT_SCANOUT_V1' not in text:
    def replace(old, new):
        global text
        assert text.count(old) == 1, old[:120]
        text = text.replace(old, new)

    replace('uint32_t connector = 0, crtc = 0, plane = 0, modeBlob = 0, currentFb = 0;',
            '// SHENG_SPLIT_SCANOUT_V1: each DSI half needs its own SSPP plane.\n'
            'uint32_t connector = 0, crtc = 0, plane = 0, secondPlane = 0, modeBlob = 0, currentFb = 0;')
    replace('connector = crtc = plane = modeBlob = currentFb = 0;',
            'connector = crtc = plane = secondPlane = modeBlob = currentFb = 0;')
    replace('i < planes->count_planes && !plane;', 'i < planes->count_planes;')
    replace('bool primary = false, rgba = false;', 'bool primary = false, overlay = false, rgba = false;')
    replace('if (!strcmp(prop->name, "type") && props->prop_values[j] == DRM_PLANE_TYPE_PRIMARY) primary = true;',
            'if (!strcmp(prop->name, "type")) {\n'
            '                            primary = props->prop_values[j] == DRM_PLANE_TYPE_PRIMARY;\n'
            '                            overlay = props->prop_values[j] == DRM_PLANE_TYPE_OVERLAY;\n'
            '                        }')
    replace('if (primary && rgba && (p->possible_crtcs & (1U << crtcIndex))) plane = p->plane_id;',
            'if (rgba && (p->possible_crtcs & (1U << crtcIndex))) {\n'
            '                if (primary && !plane) plane = p->plane_id;\n'
            '                if (overlay && !secondPlane) secondPlane = p->plane_id;\n'
            '            }')
    replace('if (!connector || !crtc || !plane || drmModeCreatePropertyBlob',
            'if (!connector || !crtc || !plane || !secondPlane || mode.hdisplay != 3048 || mode.vdisplay != 2032 || drmModeCreatePropertyBlob')
    replace('Ace5Log("discovered DSI=%u CRTC=%u plane=%u %ux%u@%u mm=%ux%u",\n'
            '        connector, crtc, plane, mode.hdisplay, mode.vdisplay, mode.vrefresh, mmWidth, mmHeight);',
            'Ace5Log("discovered Sheng dual DSI=%u CRTC=%u planes=%u,%u %ux%u@%u mm=%ux%u",\n'
            '        connector, crtc, plane, secondPlane, mode.hdisplay, mode.vdisplay, mode.vrefresh, mmWidth, mmHeight);')
    replace('if (int64_t(clientCrop.x) + clientCrop.w > b.width ||',
            'if (clientCrop.w < 2 || int64_t(clientCrop.x) + clientCrop.w > b.width ||')
    start = text.index('    PROP(plane, DRM_MODE_OBJECT_PLANE, "FB_ID", fb);')
    end = text.index('\n#undef PROP', start)
    text = text[:start] + '''    // Partition the source exactly; no gap or duplicated column at the seam.
    const int leftSourceWidth = clientCrop.w / 2;
    for (unsigned half = 0; half < 2; ++half) {
        const uint32_t target = half ? secondPlane : plane;
        const int sourceX = clientCrop.x + (half ? leftSourceWidth : 0);
        const int sourceWidth = half ? clientCrop.w - leftSourceWidth : leftSourceWidth;
        const uint32_t outputWidth = mode.hdisplay / 2;
        PROP(target, DRM_MODE_OBJECT_PLANE, "FB_ID", fb);
        PROP(target, DRM_MODE_OBJECT_PLANE, "CRTC_ID", crtc);
        PROP(target, DRM_MODE_OBJECT_PLANE, "SRC_X", uint64_t(sourceX) << 16);
        PROP(target, DRM_MODE_OBJECT_PLANE, "SRC_Y", uint64_t(clientCrop.y) << 16);
        PROP(target, DRM_MODE_OBJECT_PLANE, "SRC_W", uint64_t(sourceWidth) << 16);
        PROP(target, DRM_MODE_OBJECT_PLANE, "SRC_H", uint64_t(clientCrop.h) << 16);
        PROP(target, DRM_MODE_OBJECT_PLANE, "CRTC_X", half * outputWidth);
        PROP(target, DRM_MODE_OBJECT_PLANE, "CRTC_Y", 0);
        PROP(target, DRM_MODE_OBJECT_PLANE, "CRTC_W", outputWidth);
        PROP(target, DRM_MODE_OBJECT_PLANE, "CRTC_H", mode.vdisplay);
        PROP(target, DRM_MODE_OBJECT_PLANE, "color_fill", 0);
    }''' + text[end:]
    source.write_text(text)

if 'SHENG_FULL_POWER_OFF_V1' not in text:
    old = '''        result = Property(request, crtc, DRM_MODE_OBJECT_CRTC, "ACTIVE", 0) < 0 ? FAIL :
            drmModeAtomicCommit(drm, request, DRM_MODE_ATOMIC_ALLOW_MODESET, nullptr);
        drmModeAtomicFree(request);'''
    assert text.count(old) == 1
    text = text.replace(old, '''        // SHENG_FULL_POWER_OFF_V1: detach all objects, so reactivation
        // rebuilds the complete routing state instead of retaining a mode.
        bool valid = true;
        for (uint32_t target : {plane, secondPlane}) {
            valid &= Property(request, target, DRM_MODE_OBJECT_PLANE, "FB_ID", 0) >= 0;
            valid &= Property(request, target, DRM_MODE_OBJECT_PLANE, "CRTC_ID", 0) >= 0;
        }
        valid &= Property(request, connector, DRM_MODE_OBJECT_CONNECTOR, "CRTC_ID", 0) >= 0;
        valid &= Property(request, crtc, DRM_MODE_OBJECT_CRTC, "ACTIVE", 0) >= 0;
        valid &= Property(request, crtc, DRM_MODE_OBJECT_CRTC, "MODE_ID", 0) >= 0;
        result = valid ? drmModeAtomicCommit(drm, request, DRM_MODE_ATOMIC_ALLOW_MODESET, nullptr) : FAIL;
        drmModeAtomicFree(request);
        if (!result && currentFb) { drmModeRmFB(drm, currentFb); currentFb = 0; }''')
    source.write_text(text)

snapshot = workspace / 'compat/sheng-graphics/src/composer_vdi.cpp'
snapshot.parent.mkdir(parents=True, exist_ok=True)
snapshot.write_text(text)
print('Sheng split scanout private source staged:', snapshot)
