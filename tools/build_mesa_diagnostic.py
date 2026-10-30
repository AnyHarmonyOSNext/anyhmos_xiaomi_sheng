"""Build existing private Mesa tree with bounded native-buffer failure evidence (WSL)."""
from pathlib import Path
import subprocess, shutil, hashlib, json, gzip, os

r = Path('/mnt/c/SHENG_WORKSPACE')
base = Path('/root/hmos-work/graphics-deps')
src = base / 'source/mesa3d/src/freedreno/vulkan/tu_ohos.cc'
dest = r / 'compat/sheng-graphics/gpu-diagnostic-v1'
dest.mkdir(exist_ok=True)
before = src.read_text()
backup = dest / 'tu_ohos.before.cc'
if not backup.exists():
    backup.write_text(before)
old = ' if(!out || !tu_ohos_valid_handle(h))return VK_ERROR_INVALID_EXTERNAL_HANDLE;'
new = ''' if(!out || !tu_ohos_valid_handle(h)) {
  static unsigned invalid_count=0;
  if(invalid_count++<48)fprintf(stderr,"SHENG_NATIVE_INVALID handle=%p fd=%d native=%dx%d format=%d stride=%d size=%d usage=%llx reserve=%u/%u out=%p\\n",(const void*)h,h?h->fd:-1,h?h->width:-1,h?h->height:-1,h?h->format:-1,h?h->stride:-1,h?h->size:-1,(unsigned long long)(h?h->usage:0),h?h->reserveFds:0,h?h->reserveInts:0,(void*)out);
  return VK_ERROR_INVALID_EXTERNAL_HANDLE;
 }'''
if old in before:
    assert before.count(old) == 1
    src.write_text(before.replace(old, new))
else:
    assert 'SHENG_NATIVE_INVALID' in before
env = os.environ.copy()
env['PATH'] = str(base / 'mesa-build-env/bin') + ':' + env['PATH']
subprocess.run(['meson', 'compile', '-C', str(base / 'turnip-build'), '-j', '8'], env=env, check=True)
lib = dest / 'libvulkan_freedreno.so'
shutil.copy2(base / 'turnip-build/src/freedreno/vulkan/libvulkan_freedreno.so', lib)
subprocess.run(['/root/hmos-work/sdk-6.0.0.47/installed/native/llvm/bin/llvm-strip', str(lib)], check=True)
shutil.copy2(src, dest / 'tu_ohos.cc')
data = lib.read_bytes()
assert b'SHENG_NATIVE_INVALID' in data and b'SHENG_BIND' in data
compressed = gzip.compress(data, mtime=0)
(dest / 'libvulkan_freedreno.so.gz').write_bytes(compressed)
for i, start in enumerate(range(0, len(compressed), 900000)):
    (dest / f'gpu.part{i}').write_bytes(compressed[start:start+900000])
report = dict(bytes=len(data), sha256=hashlib.sha256(data).hexdigest(), gzip_bytes=len(compressed),
              gzip_sha256=hashlib.sha256(compressed).hexdigest(),
              mesa_commit=subprocess.check_output(['git', '-C', str(base/'source/mesa3d'), 'rev-parse', 'HEAD'], text=True).strip())
(dest / 'manifest.json').write_text(json.dumps(report, indent=2)+'\n')
print(json.dumps(report))
