"""Refresh OHOS EGL window dimensions from the real native window."""
from pathlib import Path
import subprocess, os, shutil, gzip, hashlib, json
r=Path('/mnt/c/SHENG_WORKSPACE')
b=Path('/root/hmos-work/graphics-deps')
p=b/'source/mesa3d/src/egl/drivers/dri2/platform_ohos.c'
out=r/'compat/sheng-graphics/egl-resize-v144'; out.mkdir(exist_ok=True)
old=p.read_text()
if 'ohos_refresh_window_size' not in old:
    assert hashlib.sha256(old.encode()).hexdigest()==hashlib.sha256((r/'compat/sheng-graphics/zink-cleanup-v126/platform_ohos.c').read_bytes()).hexdigest()
    (out/'platform_ohos.before.c').write_text(old)
    helper='''static void
ohos_refresh_window_size(struct dri2_egl_surface *surf)
{
   if (!surf->window)
      return;
   int width = 0, height = 0;
   if (OH_NativeWindow_NativeWindowHandleOpt(surf->window, GET_BUFFER_GEOMETRY,
                                           &height, &width) != 0 ||
       width <= 0 || height <= 0)
      return;
   if (surf->base.Width != width || surf->base.Height != height) {
      surf->base.Width = width;
      surf->base.Height = height;
      if (surf->dri_drawable)
         dri_invalidate_drawable(surf->dri_drawable);
   }
}

static EGLBoolean
ohos_query_surface(_EGLDisplay *disp, _EGLSurface *surface,
                   EGLint attribute, EGLint *value)
{
   if (attribute == EGL_WIDTH || attribute == EGL_HEIGHT)
      ohos_refresh_window_size(dri2_egl_surface(surface));
   return _eglQuerySurface(disp, surface, attribute, value);
}

'''
    marker='static EGLBoolean\nohos_swap_buffers('
    assert old.count(marker)==1
    s=old.replace(marker,helper+marker)
    s=s.replace('   driSwapBuffers(dri2_surf->dri_drawable);','   ohos_refresh_window_size(dri2_surf);\n   driSwapBuffers(dri2_surf->dri_drawable);\n   dri_invalidate_drawable(dri2_surf->dri_drawable);')
    s=s.replace('   .swap_buffers = ohos_swap_buffers,','   .swap_buffers = ohos_swap_buffers,\n   .query_surface = ohos_query_surface,')
    s=s.replace('   *x = *y = 0;\n   *w = dri2_surf->base.Width;','   ohos_refresh_window_size(dri2_surf);\n   *x = *y = 0;\n   *w = dri2_surf->base.Width;')
    p.write_text(s)
(out/'platform_ohos.c').write_text(p.read_text())
env=os.environ.copy();env['PATH']=str(b/'mesa-build-env/bin')+':'+env['PATH']
subprocess.run(['ninja','-C',str(b/'zink-build'),'src/egl/libEGL_impl.so','-j8'],check=True,env=env)
target=out/'libEGL_impl.so'; shutil.copy2(b/'zink-build/src/egl/libEGL_impl.so',target)
subprocess.run(['/root/hmos-work/sdk-6.0.0.47/installed/native/llvm/bin/llvm-strip',str(target)],check=True)
data=target.read_bytes();(out/'libEGL_impl.so.gz').write_bytes(gzip.compress(data,mtime=0))
report=dict(bytes=len(data),sha256=hashlib.sha256(data).hexdigest(),gzip_bytes=(out/'libEGL_impl.so.gz').stat().st_size,global_installed=False,changes=['query actual geometry for EGL width/height and drawable refresh','invalidate drawable after swap to observe resize'])
(out/'manifest.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report))
