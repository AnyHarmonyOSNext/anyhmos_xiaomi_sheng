"""Reproduce actual 3048x2032 import, compare visible vs padded allocation size."""
from pathlib import Path
import subprocess,json,hashlib
r=Path('/mnt/c/SHENG_WORKSPACE');base=Path('/root/hmos-work/graphics-deps')
sdk=Path('/root/hmos-work/sdk-6.0.0.47/installed/native')
s=(base/'sheng-graphics-port/gpu-port/src/native_buffer_contract.cpp').read_text()
end='VkDeviceMemory memory;VKCHECK(vkAllocateMemory(device,&mai,NULL,&memory));VKCHECK(vkBindImageMemory(device,image,memory,0));'
assert s.count(end)==1
s=s[:s.index(end)+len(end)]+ '\n printf("FULLSIZE_IMPORT_OK stride=%d size=%d\\n",h->stride,total);_exit(0);}\n'
s=s.replace('#include "vertex.inc"','').replace('#include "fragment.inc"','')
s=s.replace('CHECK(argc==2);','CHECK(argc==2||argc==3);')
s=s.replace('constexpr int W=128,H=96,logical=W*H*4,total=logical+4096;',
 'constexpr int W=3048,H=2032,logical=12288*H;int total=argc==3?12288*2048:logical;printf("LAYOUT_PROBE w=%d h=%d stride=12288 size=%d padded=%d\\n",W,H,total,argc==3);')
s=s.replace('h->stride=W*4;','h->stride=12288;')
dest=r/'compat/sheng-graphics/native-layout-probe-v1';dest.mkdir(exist_ok=True)
(dest/'native_layout_probe.cpp').write_text(s)
cmd=[str(sdk/'llvm/bin/clang++'),'--target=aarch64-linux-ohos','-std=c++17','-O2','-fno-exceptions','-fno-rtti','-nostdlib++','-include',str(base/'sheng-graphics-port/tests/platform_cpp_config.h'),'-I'+str(base/'source/mesa3d/include'),str(dest/'native_layout_probe.cpp'),str(r/'work/donor-hdi-link/libc++.so'),'-o',str(dest/'native_layout_probe')]
subprocess.run(cmd,check=True);subprocess.run([str(sdk/'llvm/bin/llvm-strip'),str(dest/'native_layout_probe')],check=True)
p=dest/'native_layout_probe';report={'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'scope':'real DMA heap + original SurfaceBuffer fixture + fullsize Vulkan bind; not allocator IPC or physical scanout'}
(dest/'manifest.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report))
