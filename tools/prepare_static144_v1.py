"""Select the real kernel144 timing before framework enumeration, no mode churn."""
from pathlib import Path
r=Path(__file__).resolve().parent.parent;d=r/'compat/sheng-graphics/static144-v1';d.mkdir(exist_ok=True)
s=(r/'compat/sheng-graphics/framepacing-v1/composer_vdi.cpp').read_text(encoding='utf-8')
needle='            connector = c->connector_id; mmWidth = c->mmWidth; mmHeight = c->mmHeight;'
assert s.count(needle)==1
s=s.replace(needle,'''            bool native144 = false;
            for (uint32_t i = 0; i < displayModes.size(); ++i) {
                if (displayModes[i].vrefresh == 144) {
                    selectedMode = i; mode = displayModes[i]; native144 = true; break;
                }
            }
            if (!native144) { drmModeFreeConnector(c); drmModeFreeResources(resources); CleanupDrm(); return FAIL; }
''' +needle)
needle='    if (!connector || !crtc || !plane || !secondPlane || mode.hdisplay != 3048'
pos=s.index(needle)
s=s[:pos]+'''    // A complete OFF->ON is required before the initial144 modeset. Do not
    // attempt the failed v83 seamless120->144 transition on active scanout.
    auto *existing = crtc ? drmModeGetCrtc(drm, crtc) : nullptr;
    bool detach = existing && existing->mode_valid;
    if (existing) drmModeFreeCrtc(existing);
    if (detach) {
        auto *off = drmModeAtomicAlloc(); bool valid = off != nullptr;
        auto *routes = drmModeGetPlaneResources(drm);
        if (!routes) valid = false;
        if (routes) {
            for (uint32_t i=0;i<routes->count_planes;++i) {
                auto *route=drmModeGetPlane(drm,routes->planes[i]);
                if (!route) { valid=false; continue; }
                if (route->crtc_id==crtc && off) {
                    valid &= Property(off,route->plane_id,DRM_MODE_OBJECT_PLANE,"FB_ID",0)>=0;
                    valid &= Property(off,route->plane_id,DRM_MODE_OBJECT_PLANE,"CRTC_ID",0)>=0;
                }
                drmModeFreePlane(route);
            }
            drmModeFreePlaneResources(routes);
        }
        if (off) {
            valid &= Property(off,connector,DRM_MODE_OBJECT_CONNECTOR,"CRTC_ID",0)>=0;
            valid &= Property(off,crtc,DRM_MODE_OBJECT_CRTC,"ACTIVE",0)>=0;
            valid &= Property(off,crtc,DRM_MODE_OBJECT_CRTC,"MODE_ID",0)>=0;
        }
        int rc=valid?drmModeAtomicCommit(drm,off,DRM_MODE_ATOMIC_ALLOW_MODESET,nullptr):-1;
        if(off)drmModeAtomicFree(off);
        if(rc){Log("static144 initial detach failed");CleanupDrm();return FAIL;}
        usleep(100000);
    }
''' +s[pos:]
(d/'composer_vdi.cpp').write_text(s,encoding='utf-8',newline='\n')
s=(r/'tools/build_framepacing_v1.py').read_text(encoding='utf-8').replace('framepacing-v1','static144-v1')
(r/'tools/build_static144_v1.py').write_text(s,encoding='utf-8',newline='\n')
print('static144 source staged; actual hardware acceptance pending')
