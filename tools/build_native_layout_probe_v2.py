"""Match original NativeBufferUtils image usage, pNext and BindImageMemory2."""
from pathlib import Path
import subprocess,hashlib,json
r=Path('/mnt/c/SHENG_WORKSPACE');base=Path('/root/hmos-work/graphics-deps');sdk=Path('/root/hmos-work/sdk-6.0.0.47/installed/native')
s=(r/'compat/sheng-graphics/native-layout-probe-v1/native_layout_probe.cpp').read_text()
s=s.replace('h->usage=0x70b;','h->usage=0x708;').replace('DEV(vkBindImageMemory);','DEV(vkBindImageMemory2);')
s=s.replace('VkImage image;VKCHECK(vkCreateImage(device,&imageInfo,NULL,&image));',
 'VkExternalFormatOHOS externalFormat{VK_STRUCTURE_TYPE_EXTERNAL_FORMAT_OHOS};ext.pNext=&externalFormat;imageInfo.usage|=VK_IMAGE_USAGE_TRANSFER_SRC_BIT|VK_IMAGE_USAGE_TRANSFER_DST_BIT|VK_IMAGE_USAGE_INPUT_ATTACHMENT_BIT;VkImage image;VKCHECK(vkCreateImage(device,&imageInfo,NULL,&image));')
s=s.replace('VKCHECK(vkBindImageMemory(device,image,memory,0));',
 'VkBindImageMemoryInfo bind{VK_STRUCTURE_TYPE_BIND_IMAGE_MEMORY_INFO};bind.image=image;bind.memory=memory;VKCHECK(vkBindImageMemory2(device,1,&bind));')
dest=r/'compat/sheng-graphics/native-layout-probe-v2';dest.mkdir(exist_ok=True);(dest/'native_layout_probe.cpp').write_text(s)
cmd=[str(sdk/'llvm/bin/clang++'),'--target=aarch64-linux-ohos','-std=c++17','-O2','-fno-exceptions','-fno-rtti','-nostdlib++','-include',str(base/'sheng-graphics-port/tests/platform_cpp_config.h'),'-I'+str(base/'source/mesa3d/include'),str(dest/'native_layout_probe.cpp'),str(r/'work/donor-hdi-link/libc++.so'),'-o',str(dest/'native_layout_probe')]
subprocess.run(cmd,check=True);subprocess.run([str(sdk/'llvm/bin/llvm-strip'),str(dest/'native_layout_probe')],check=True)
p=dest/'native_layout_probe';report={'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'scope':'actual Rosen usage/pNext and BindImageMemory2, original SurfaceBuffer handle fixture; no scanout claim'}
(dest/'manifest.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report))
