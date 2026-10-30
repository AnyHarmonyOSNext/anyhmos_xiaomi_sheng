"""Fix OHOS platform ownership of EGL display creation and failure cleanup."""
from pathlib import Path
import subprocess, os, shutil, hashlib, gzip, json
r=Path(__file__).resolve().parent.parent
b=Path('/root/hmos-work/graphics-deps')
p=b/'source/mesa3d/src/egl/drivers/dri2/platform_ohos.c'
out=r/'compat/sheng-graphics/zink-cleanup-v126';out.mkdir(exist_ok=True)
old=p.read_text()
start=old.index('dri2_initialize_ohos(_EGLDisplay *disp)')
head,tail=old[:start],old[start:]
a='struct dri2_egl_display *dri2_dpy = dri2_display_create(disp);'
z='struct dri2_egl_display *dri2_dpy = dri2_egl_display(disp);'
if a in tail:
    assert tail.count(a)==1
    (out/'platform_ohos.before.c').write_text(old)
    tail=tail.replace(a,z)
    assert tail.count('cleanup:\n   dri2_display_destroy(disp);')==1
    tail=tail.replace('cleanup:\n   dri2_display_destroy(disp);','cleanup:\n   /* The parent dri2_initialize owns display creation and destruction. */')
    p.write_text(head+tail)
else:
    assert z in tail and 'parent dri2_initialize owns' in tail
(out/'platform_ohos.c').write_text(p.read_text())
env=os.environ.copy();env['PATH']=str(b/'mesa-build-env/bin')+':'+env['PATH']
subprocess.run(['ninja','-C',str(b/'zink-build'),'src/egl/libEGL_impl.so','-j8'],check=True,env=env)
sdk=Path('/root/hmos-work/sdk-6.0.0.47/installed/native')
target=out/'libEGL_impl.so';shutil.copy2(b/'zink-build/src/egl/libEGL_impl.so',target)
subprocess.run([str(sdk/'llvm/bin/llvm-strip'),str(target)],check=True)
data=target.read_bytes();(out/'libEGL_impl.so.gz').write_bytes(gzip.compress(data,mtime=0))
report=dict(bytes=len(data),sha256=hashlib.sha256(data).hexdigest(),gzip_bytes=(out/'libEGL_impl.so.gz').stat().st_size,changes=['reuse parent display','leave failure cleanup to parent'],global_tested=False)
(out/'manifest.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report))
