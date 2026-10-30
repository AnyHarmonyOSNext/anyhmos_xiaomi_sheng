"""Bounded diagnostic geometry transitions and EGL caller locations; RAM only."""
from pathlib import Path
import subprocess, os, shutil, gzip, hashlib, json
r=Path('/mnt/c/SHENG_WORKSPACE')
b=Path('/root/hmos-work/graphics-deps')
p=b/'source/mesa3d/src/egl/drivers/dri2/platform_ohos.c'
out=r/'compat/sheng-graphics/egl-trace2-v144';out.mkdir(exist_ok=True)
s=(r/'compat/sheng-graphics/egl-default-v144/platform_ohos.c').read_text()
s=s.replace('#include <stdlib.h>', '#include <stdlib.h>\n#include <stdio.h>\n#include <unistd.h>\n#include <dlfcn.h>')
marker='static bool\nohos_resolve_geometry'
helper='''static void
ohos_geometry_trace(const char *stage, void *window, int width, int height, void *caller)
{
   static unsigned count;
   if (__atomic_fetch_add(&count, 1, __ATOMIC_RELAXED) >= 400)
      return;
   Dl_info info = {0};
   dladdr(caller, &info);
   FILE *f = fopen("/dev/v144-egl-trace2.log", "a");
   if (f) {
      fprintf(f, "EGL2 pid=%d stage=%s win=%p size=%dx%d caller=%p %s+%lx\\n",
              getpid(), stage, window, width, height, caller,
              info.dli_fname ? info.dli_fname : "?",
              (unsigned long)((char *)caller-(char *)info.dli_fbase));
      fclose(f);
   }
}

'''
assert s.count(marker)==1;s=s.replace(marker,helper+marker)
s=s.replace('   return &dri2_surf->base;', '   ohos_geometry_trace("create", window, dri2_surf->base.Width, dri2_surf->base.Height, __builtin_return_address(0));\n   return &dri2_surf->base;')
s=s.replace('   if (attribute == EGL_WIDTH || attribute == EGL_HEIGHT)\n      ohos_refresh_window_size(dri2_egl_surface(surface));', '''   if (attribute == EGL_WIDTH || attribute == EGL_HEIGHT) {
      ohos_refresh_window_size(dri2_egl_surface(surface));
      ohos_geometry_trace(attribute == EGL_WIDTH ? "queryW" : "queryH",
                          dri2_egl_surface(surface)->window, surface->Width,
                          surface->Height, __builtin_return_address(0));
   }''')
s=s.replace('   driSwapBuffers(dri2_surf->dri_drawable);', '''   ohos_geometry_trace("swap-before", dri2_surf->window, dri2_surf->base.Width, dri2_surf->base.Height, __builtin_return_address(0));
   driSwapBuffers(dri2_surf->dri_drawable);
   ohos_refresh_window_size(dri2_surf);
   ohos_geometry_trace("swap-after", dri2_surf->window, dri2_surf->base.Width, dri2_surf->base.Height, __builtin_return_address(0));''')
s=s.replace('   *x = *y = 0;', '   ohos_geometry_trace("drawable", dri2_surf->window, dri2_surf->base.Width, dri2_surf->base.Height, __builtin_return_address(0));\n   *x = *y = 0;')
p.write_text(s);(out/'platform_ohos.c').write_text(s)
env=os.environ.copy();env['PATH']=str(b/'mesa-build-env/bin')+':'+env['PATH']
subprocess.run(['ninja','-C',str(b/'zink-build'),'src/egl/libEGL_impl.so','-j8'],check=True,env=env)
target=out/'libEGL_impl.so';shutil.copy2(b/'zink-build/src/egl/libEGL_impl.so',target)
subprocess.run(['/root/hmos-work/sdk-6.0.0.47/installed/native/llvm/bin/llvm-strip',str(target)],check=True)
data=target.read_bytes();(out/'libEGL_impl.so.gz').write_bytes(gzip.compress(data,mtime=0))
report=dict(bytes=len(data),sha256=hashlib.sha256(data).hexdigest(),diagnostic_only=True)
(out/'manifest.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report))
