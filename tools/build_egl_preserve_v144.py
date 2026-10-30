"""Preserve a newer native producer size across presentation of an old drawable."""
from pathlib import Path
import subprocess, os, shutil, gzip, hashlib, json
r=Path('/mnt/c/SHENG_WORKSPACE')
b=Path('/root/hmos-work/graphics-deps')
p=b/'source/mesa3d/src/egl/drivers/dri2/platform_ohos.c'
out=r/'compat/sheng-graphics/egl-preserve-v144';out.mkdir(exist_ok=True)
s=(r/'compat/sheng-graphics/egl-default-v144/platform_ohos.c').read_text()
s=s.replace('#include "dri_util.h"','#include "dri_util.h"\n#include "dri_drawable.h"')
old='''   ohos_refresh_window_size(dri2_surf);
   driSwapBuffers(dri2_surf->dri_drawable);
   dri_invalidate_drawable(dri2_surf->dri_drawable);'''
new='''   ohos_refresh_window_size(dri2_surf);
   const int requested_width = dri2_surf->base.Width;
   const int requested_height = dri2_surf->base.Height;
   const int drawable_width = dri2_surf->dri_drawable->w;
   const int drawable_height = dri2_surf->dri_drawable->h;
   driSwapBuffers(dri2_surf->dri_drawable);

   /* A deferred first swap can create the old-size Vulkan swapchain after
    * the producer has already requested a new size. The OHOS WSI then writes
    * that old extent to the native window. Preserve the newer request only
    * when the write exactly matches the stale drawable we just presented. */
   if (dri2_surf->window && drawable_width > 0 && drawable_height > 0 &&
       (requested_width != drawable_width || requested_height != drawable_height)) {
      int width = 0, height = 0;
      if (OH_NativeWindow_NativeWindowHandleOpt(dri2_surf->window,
              GET_BUFFER_GEOMETRY, &height, &width) == 0 &&
          width == drawable_width && height == drawable_height) {
         if (OH_NativeWindow_NativeWindowHandleOpt(dri2_surf->window,
                 SET_BUFFER_GEOMETRY, requested_width, requested_height) != 0)
            return _eglError(EGL_BAD_NATIVE_WINDOW, "restore producer geometry");
      }
   }
   ohos_refresh_window_size(dri2_surf);
   dri_invalidate_drawable(dri2_surf->dri_drawable);'''
assert s.count(old)==1;s=s.replace(old,new)
p.write_text(s);(out/'platform_ohos.c').write_text(s)
env=os.environ.copy();env['PATH']=str(b/'mesa-build-env/bin')+':'+env['PATH']
subprocess.run(['ninja','-C',str(b/'zink-build'),'src/egl/libEGL_impl.so','-j8'],check=True,env=env)
target=out/'libEGL_impl.so';shutil.copy2(b/'zink-build/src/egl/libEGL_impl.so',target)
subprocess.run(['/root/hmos-work/sdk-6.0.0.47/installed/native/llvm/bin/llvm-strip',str(target)],check=True)
data=target.read_bytes();(out/'libEGL_impl.so.gz').write_bytes(gzip.compress(data,mtime=0))
report=dict(bytes=len(data),sha256=hashlib.sha256(data).hexdigest(),persistent_installed=False)
(out/'manifest.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report))
