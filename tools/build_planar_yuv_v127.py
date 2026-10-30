"""Add explicit I420/YV12 planes without changing existing NV12 or RGB."""
from pathlib import Path
import runpy, subprocess, os, hashlib, json, gzip
r=Path(__file__).resolve().parent.parent; b=Path('/root/hmos-work/graphics-deps')
port=b/'sheng-graphics-port'; sdk=Path('/root/hmos-work/sdk-6.0.0.47/installed/native')
out=r/'compat/sheng-graphics/planar-v127';out.mkdir(exist_ok=True)
os.environ.update(ANYHARMONYOS_OHOS_SOURCE=str(b/'source'),ANYHARMONYOS_STAGE=str(b/'stage'),ANYHARMONYOS_ROM_SYSTEM_LIBS=str(r/'work/hmos_system/system/system/lib64'),ANYHARMONYOS_SDK=str(sdk))
cfg=runpy.run_path(str(port/'tools/build_adapter.py'))
s=(r/'compat/sheng-graphics/metadata-v124/buffer_vdi.cpp').read_text()
s=s.replace('bool IsSemiPlanar420(uint32_t format) { return format == 24 || format == 25; }','bool IsPlanar420(uint32_t format) { return format == 28 || format == 29; }\nbool IsYuv420(uint32_t format) { return format == 24 || format == 25 || IsPlanar420(format); }')
s=s.replace('IsSemiPlanar420(', 'IsYuv420(')
old='''            layout.planes.push_back({uint32_t(h.stride) * uint32_t(h.height),
                uint32_t(h.stride), uint32_t(h.height / 2)});'''
assert s.count(old)==1
s=s.replace(old,'''            const uint32_t luma = uint32_t(h.stride) * uint32_t(h.height);
            if (IsPlanar420(h.format)) {
                const uint32_t chromaStride = uint32_t(h.stride / 2);
                const uint32_t chromaSize = chromaStride * uint32_t(h.height / 2);
                // Plane order follows native memory order: Y,U,V or Y,V,U.
                layout.planes.push_back({luma, chromaStride, uint32_t(h.height / 2)});
                layout.planes.push_back({luma + chromaSize, chromaStride, uint32_t(h.height / 2)});
            } else {
                layout.planes.push_back({luma, uint32_t(h.stride), uint32_t(h.height / 2)});
            }''')
(out/'buffer_vdi.cpp').write_text(s)
report={}
target=out/'libdisplay_buffer_vdi_impl.z.so'
subprocess.run(cfg['COMMON']+['-I'+str(port/'adapter'),'-DACE5_LINEAR_STRIDE_ALIGNMENT=128','-shared','-fPIC','-Wl,-z,defs','-Wl,-soname,libdisplay_buffer_vdi_impl.z.so',str(out/'buffer_vdi.cpp'),str(cfg['CPP']),'-o',str(target)],check=True)
subprocess.run([str(sdk/'llvm/bin/llvm-strip'),str(target)],check=True)
src=b/'source/mesa3d/src'; p=src/'freedreno/vulkan/tu_ohos.cc'
before=out/'tu_ohos.cc.before'
if not before.exists():before.write_bytes(p.read_bytes())
s=before.read_text()
s=s.replace(' case 24: return VK_FORMAT_G8_B8R8_2PLANE_420_UNORM;', ' case 28: case 29: return VK_FORMAT_G8_B8_R8_3PLANE_420_UNORM;\n case 24: return VK_FORMAT_G8_B8R8_2PLANE_420_UNORM;')
s=s.replace('f==VK_FORMAT_G8_B8R8_2PLANE_420_UNORM;', 'f==VK_FORMAT_G8_B8R8_2PLANE_420_UNORM || f==VK_FORMAT_G8_B8_R8_3PLANE_420_UNORM;')
s=s.replace('bool yuv=h->format==24;', 'bool yuv=h->format==24 || h->format==28 || h->format==29;')
s=s.replace('VkSubresourceLayout planes[2]={};','VkSubresourceLayout planes[3]={};')
needle=' if(h->format==24){planes[1].offset=planes[0].size;planes[1].rowPitch=h->stride;planes[1].size=planes[0].size/2;}'
assert s.count(needle)==1
s=s.replace(needle,needle+'''
 if(h->format==28 || h->format==29) {
  const uint64_t chromaSize=uint64_t(h->stride/2)*(h->height/2);
  planes[1].offset=planes[0].size+(h->format==29?chromaSize:0);
  planes[2].offset=planes[0].size+(h->format==28?chromaSize:0);
  planes[1].rowPitch=planes[2].rowPitch=h->stride/2;
  planes[1].size=planes[2].size=chromaSize;
 }''')
s=s.replace('  f->format=h->format==24?VK_FORMAT_UNDEFINED:ohos_format(h->format);\n  f->externalFormat=h->format==24?24:0;', '  const bool yuv=h->format==24 || h->format==28 || h->format==29;\n  f->format=yuv?VK_FORMAT_UNDEFINED:ohos_format(h->format);\n  f->externalFormat=yuv?h->format:0;')
s=s.replace('f->suggestedYcbcrModel=h->format==24?', 'f->suggestedYcbcrModel=yuv?').replace('f->suggestedYcbcrRange=h->format==24?', 'f->suggestedYcbcrRange=yuv?')
p.write_text(s); (out/'tu_ohos.cc').write_text(s)
for rel in ['freedreno/vulkan/tu_image.cc','vulkan/runtime/vk_ycbcr_conversion.c']:
 p=src/rel;before=out/(p.name+'.before')
 if not before.exists():before.write_bytes(p.read_bytes())
 s=before.read_text()
 if p.name=='tu_image.cc':
  s=s.replace('external->externalFormat != 24 ||', '(external->externalFormat != 24 && external->externalFormat != 28 && external->externalFormat != 29) ||')
  s=s.replace('resolved_info.format = VK_FORMAT_G8_B8R8_2PLANE_420_UNORM;', 'resolved_info.format = external->externalFormat == 24 ? VK_FORMAT_G8_B8R8_2PLANE_420_UNORM : VK_FORMAT_G8_B8_R8_3PLANE_420_UNORM;')
 else:
  s=s.replace('ohos_ext_info->externalFormat != 24 ||', '(ohos_ext_info->externalFormat != 24 && ohos_ext_info->externalFormat != 28 && ohos_ext_info->externalFormat != 29) ||')
  s=s.replace('state->format = VK_FORMAT_G8_B8R8_2PLANE_420_UNORM;', 'state->format = ohos_ext_info->externalFormat == 24 ? VK_FORMAT_G8_B8R8_2PLANE_420_UNORM : VK_FORMAT_G8_B8_R8_3PLANE_420_UNORM;')
 p.write_text(s); (out/p.name).write_text(s)
env=os.environ.copy();env['PATH']=str(b/'mesa-build-env/bin')+':'+env['PATH']
subprocess.run(['ninja','-C',str(b/'turnip-build'),'-j8','src/freedreno/vulkan/libvulkan_freedreno.so'],env=env,check=True)
target=out/'libvulkan_freedreno.so';target.write_bytes((b/'turnip-build/src/freedreno/vulkan/libvulkan_freedreno.so').read_bytes())
subprocess.run([str(sdk/'llvm/bin/llvm-strip'),str(target)],check=True)
packed=gzip.compress(target.read_bytes(),mtime=0);(out/'libvulkan_freedreno.so.gz').write_bytes(packed)
for name in ['libdisplay_buffer_vdi_impl.z.so','libvulkan_freedreno.so','libvulkan_freedreno.so.gz']:
 data=(out/name).read_bytes(); report[name]=dict(bytes=len(data),sha256=hashlib.sha256(data).hexdigest())
(out/'manifest.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report))
