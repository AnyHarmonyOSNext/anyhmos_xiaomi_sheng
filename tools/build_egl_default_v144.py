from pathlib import Path
import subprocess, os, shutil, gzip, hashlib, json
r=Path('/mnt/c/SHENG_WORKSPACE')
b=Path('/root/hmos-work/graphics-deps')
p=b/'source/mesa3d/src/egl/drivers/dri2/platform_ohos.c'
out=r/'compat/sheng-graphics/egl-default-v144';out.mkdir(exist_ok=True)
s=p.read_text()
if 'ohos_resolve_geometry' not in s:
    (out/'platform_ohos.before.c').write_text(s)
    mark='static _EGLSurface *\nohos_create_surface'
    helper='''/* Native Window keeps an explicit producer size separate from the consumer
 * default. A zero producer size means use the original consumer dimensions. */
extern int32_t NativeWindowGetDefaultWidthAndHeight(struct NativeWindow *,
                                                  int32_t *, int32_t *);
static bool
ohos_resolve_geometry(struct NativeWindow *window, int *width, int *height)
{
   if (OH_NativeWindow_NativeWindowHandleOpt(window, GET_BUFFER_GEOMETRY,
                                           height, width) != 0)
      return false;
   if ((*width <= 0 || *height <= 0) &&
       NativeWindowGetDefaultWidthAndHeight(window, width, height) != 0)
      return false;
   return *width > 0 && *height > 0;
}

'''
    assert s.count(mark)==1;s=s.replace(mark,helper+mark)
    old='''      OH_NativeWindow_NativeWindowHandleOpt(native_window, GET_BUFFER_GEOMETRY,
                                            &dri2_surf->base.Height,
                                            &dri2_surf->base.Width);'''
    new='''      if (!ohos_resolve_geometry(window, &dri2_surf->base.Width,
                                 &dri2_surf->base.Height)) {
         _eglError(EGL_BAD_NATIVE_WINDOW, "OHOS window has no valid size");
         goto cleanup_surface;
      }'''
    assert s.count(old)==1;s=s.replace(old,new)
    old='''   if (OH_NativeWindow_NativeWindowHandleOpt(surf->window, GET_BUFFER_GEOMETRY,
                                           &height, &width) != 0 ||
       width <= 0 || height <= 0)'''
    assert s.count(old)==1;s=s.replace(old,'   if (!ohos_resolve_geometry(surf->window, &width, &height))')
    p.write_text(s)
(out/'platform_ohos.c').write_text(s)
env=os.environ.copy();env['PATH']=str(b/'mesa-build-env/bin')+':'+env['PATH']
subprocess.run(['ninja','-C',str(b/'zink-build'),'src/egl/libEGL_impl.so','-j8'],check=True,env=env)
target=out/'libEGL_impl.so';shutil.copy2(b/'zink-build/src/egl/libEGL_impl.so',target)
subprocess.run(['/root/hmos-work/sdk-6.0.0.47/installed/native/llvm/bin/llvm-strip',str(target)],check=True)
data=target.read_bytes();(out/'libEGL_impl.so.gz').write_bytes(gzip.compress(data,mtime=0))
report=dict(bytes=len(data),sha256=hashlib.sha256(data).hexdigest(),gzip_bytes=(out/'libEGL_impl.so.gz').stat().st_size,persistent_installed=False)
(out/'manifest.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report))
