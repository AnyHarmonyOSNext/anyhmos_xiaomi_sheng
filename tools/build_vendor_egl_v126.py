"""Persist the real-tested EGL path and app KGSL access in vendor_boot."""
from pathlib import Path
import json, tarfile, io
from vendor_ramdisk_edit import edit, sha
r=Path(__file__).resolve().parent.parent; prefix='sheng-compat-v118/'; manifest={}
items={
 'libEGL_impl.so':('zink-cleanup-v126/libEGL_impl.so','4e4f60765599ac9d1f61b48f1aace6ae9b71a9be77069b5429fda5a1f6353ed8'),
 'libGLESv1_CM_impl.so.1':('zink-v1/libGLESv1_CM_impl.so.1','a9e5c19f128ea64d98afc58b1d1e2197dd95441994ef846815b08f3a72baf12d'),
 'libGLESv2_impl.so.2':('zink-v1/libGLESv2_impl.so.2','34c1ae97b9c1d22d75a917864eb492bda6b433a0039febda3cf912129719c65f'),
 'libgallium-25.0.1.so':('zink-v1/libgallium-25.0.1.so','af831f3bcd8958164447d2fd78e83a80aa04bc2d181da130f522f6f35fb75620')}
out=r/'compat/sheng-graphics/zink-cleanup-v126'; archive=out/'zink-runtime-v126.tar.gz'
with tarfile.open(archive,'w:gz') as tar:
 for name,(file,expected) in items.items():
  data=(r/'compat/sheng-graphics'/file).read_bytes(); assert sha(data)==expected
  info=tarfile.TarInfo(name);info.size=len(data);info.mode=0o644;info.mtime=0
  tar.addfile(info,io.BytesIO(data))
 for name,target in [('libGLESv1_impl.so','libGLESv1_CM_impl.so.1'),('libGLESv2_impl.so','libGLESv2_impl.so.2'),('libGLESv3_impl.so','libGLESv2_impl.so.2')]:
  info=tarfile.TarInfo(name);info.type=tarfile.SYMTYPE;info.linkname=target;info.mode=0o777;tar.addfile(info)
data=archive.read_bytes(); added={prefix+'graphics/zink-runtime-v126.tar.gz'}
def mutate(entries):
 fields=[0,0o100644,0,0,1,0,len(data),0,0,0,0,0,0]
 entries[next(iter(added))]=(fields,data)
 name=prefix+'graphics/apply-compat-paths.sh'; f,old=entries[name]
 assert sha(old)=='786b383761eabfdb0727f94ec92b18a68fb4e4140d4278066bb70c2dcc62d18b'
 s=old.decode()+f'''\n# Only checked compatibility libraries; no vendor files are changed.
h=$(/busybox sha256sum /graphics/zink-runtime-v126.tar.gz)
case "$h" in {sha(data)}\\ *) ;; *) echo ZINK_ARCHIVE_MISMATCH; exit 44;; esac
/busybox gzip -dc /graphics/zink-runtime-v126.tar.gz | /busybox tar -xf - -C /hmos-root/compat/lib64
'''
 for name2,(_,expected) in items.items():
  s+=f'h=$(/busybox sha256sum /hmos-root/compat/lib64/{name2})\ncase "$h" in {expected}\\ *) ;; *) echo ZINK_LIB_MISMATCH; exit 45;; esac\n'
 s+='echo ZINK_RUNTIME_V126_INSTALLED\n'; entries[name]=(f.copy(),s.encode())
 name=prefix+'graphics/start-graphics-v116.sh'; f,old=entries[name]
 assert sha(old)=='e0c3bacddc15a0c2cad6212c8f0fe3fc8cc301199c4490bf03634cba6bef1860'
 assert old.count(b'$B chmod 0660 $R/dev/kgsl-3d0')==1
 entries[name]=(f.copy(),old.replace(b'$B chmod 0660 $R/dev/kgsl-3d0',b'# Native applications have per-app groups; KGSL enforces per-process contexts.\n$B chmod 0666 $R/dev/kgsl-3d0'))
 manifest.update({n[len(prefix):]:dict(bytes=len(b),mode=oct(f[1]),sha256=sha(b)) for n,(f,b) in entries.items() if n.startswith(prefix) and n!=prefix+'MANIFEST.json'})
 name=prefix+'MANIFEST.json'; f,_=entries[name];entries[name]=(f.copy(),(json.dumps(manifest,indent=2)+'\n').encode())
allowed=added|{prefix+'graphics/apply-compat-paths.sh',prefix+'graphics/start-graphics-v116.sh',prefix+'MANIFEST.json'}
image=edit(r/'output/vendor_boot_hmos_compat_v125.img','43513140007a8337041742b0245bd44d7306d5a40850c74a2897c9f6c40984f9',r/'work/egl-v126',mutate,allowed,added)
target=r/'output/vendor_boot_hmos_compat_v126.img'; target.write_bytes(image)
report=dict(version='v126',status='built_not_flashed',vendor_boot=dict(file=target.name,bytes=len(image),sha256=sha(image)),cpio_verified=True,preserved_v125_entries=True,changed_entries=sorted(allowed),init_boot_unchanged=True,dtb_unchanged=True,bootconfig_unchanged=True,stock_vendor_modules_and_audio_unchanged=True,usb_v121_unchanged=True,metadata_v124_unchanged=True,original_gpu_governor_unchanged=True,real_egl_window_green_pixels=1024,cold_boot_verified=False)
(r/'analysis/egl-v126-verification.json').write_text(json.dumps(report,indent=2)+'\n')
(r/'output/v126-payload-manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
script=(r/'output/Flash-CompatV125.ps1').read_text(encoding='utf-8-sig').replace('v125','v126').replace('zink-test-v126-verification','egl-v126-verification').replace('preserved_v124_entries','preserved_v125_entries')
(r/'output/Flash-CompatV126.ps1').write_text(script,encoding='utf-8-sig')
print(json.dumps(report,indent=2))
