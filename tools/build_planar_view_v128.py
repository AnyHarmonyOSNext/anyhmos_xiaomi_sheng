"""Complete planar native imports at the image-view validation boundary."""
from pathlib import Path
import subprocess,os,hashlib,gzip,json
r=Path(__file__).resolve().parent.parent;b=Path('/root/hmos-work/graphics-deps');sdk=Path('/root/hmos-work/sdk-6.0.0.47/installed/native')
out=r/'compat/sheng-graphics/planar-view-v128';out.mkdir(exist_ok=True)
p=b/'source/mesa3d/src/freedreno/vulkan/tu_image.cc'
s=(r/'compat/sheng-graphics/planar-v127/tu_image.cc').read_text()
old='''      if (image->vk.format != VK_FORMAT_G8_B8R8_2PLANE_420_UNORM)
         return VK_ERROR_FORMAT_NOT_SUPPORTED;'''
assert s.count(old)==1
s=s.replace(old,'''      if (image->vk.format != VK_FORMAT_G8_B8R8_2PLANE_420_UNORM &&
          image->vk.format != VK_FORMAT_G8_B8_R8_3PLANE_420_UNORM)
         return VK_ERROR_FORMAT_NOT_SUPPORTED;''')
p.write_text(s);(out/'tu_image.cc').write_text(s)
env=os.environ.copy();env['PATH']=str(b/'mesa-build-env/bin')+':'+env['PATH']
subprocess.run(['ninja','-C',str(b/'turnip-build'),'-j8','src/freedreno/vulkan/libvulkan_freedreno.so'],env=env,check=True)
target=out/'libvulkan_freedreno.so';target.write_bytes((b/'turnip-build/src/freedreno/vulkan/libvulkan_freedreno.so').read_bytes())
subprocess.run([str(sdk/'llvm/bin/llvm-strip'),str(target)],check=True)
(out/'libvulkan_freedreno.so.gz').write_bytes(gzip.compress(target.read_bytes(),mtime=0))
report={name:dict(bytes=(out/name).stat().st_size,sha256=hashlib.sha256((out/name).read_bytes()).hexdigest()) for name in ['libvulkan_freedreno.so','libvulkan_freedreno.so.gz']}
(out/'manifest.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report))
