from pathlib import Path
import subprocess,os,shutil,gzip,hashlib,json
r=Path('/mnt/c/SHENG_WORKSPACE');b=Path('/root/hmos-work/graphics-deps')
p=b/'source/mesa3d/src/egl/drivers/dri2/platform_ohos.c'
out=r/'compat/sheng-graphics/egl-trace-v144';out.mkdir(exist_ok=True)
s=p.read_text()
if 'SHENG_EGL_GEOMETRY' not in s:
 (out/'platform_ohos.before.c').write_text(s)
 s=s.replace('#include <stdlib.h>','#include <stdlib.h>\n#include <stdio.h>\n#include <unistd.h>')
 old='''   return *width > 0 && *height > 0;
}'''
 new='''   static unsigned trace_count;
   if (__atomic_fetch_add(&trace_count, 1, __ATOMIC_RELAXED) < 40) {
      FILE *f = fopen("/data/local/tmp/v144-egl-geometry.log", "a");
      if (f) {
         fprintf(f, "SHENG_EGL_GEOMETRY pid=%d window=%p size=%dx%d\\n",
                 getpid(), (void *)window, *width, *height);
         fclose(f);
      }
   }
   return *width > 0 && *height > 0;
}'''
 assert s.count(old)==1;s=s.replace(old,new)
 p.write_text(s)
(out/'platform_ohos.c').write_text(s)
env=os.environ.copy();env['PATH']=str(b/'mesa-build-env/bin')+':'+env['PATH']
subprocess.run(['ninja','-C',str(b/'zink-build'),'src/egl/libEGL_impl.so','-j8'],check=True,env=env)
target=out/'libEGL_impl.so';shutil.copy2(b/'zink-build/src/egl/libEGL_impl.so',target)
subprocess.run(['/root/hmos-work/sdk-6.0.0.47/installed/native/llvm/bin/llvm-strip',str(target)],check=True)
data=target.read_bytes();(out/'libEGL_impl.so.gz').write_bytes(gzip.compress(data,mtime=0))
report=dict(bytes=len(data),sha256=hashlib.sha256(data).hexdigest(),diagnostic_only=True)
(out/'manifest.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report))
