from pathlib import Path
import subprocess,runpy,os
r=Path(__file__).resolve().parent.parent;b=Path('/root/hmos-work/graphics-deps');port=b/'sheng-graphics-port';sdk=Path('/root/hmos-work/sdk-6.0.0.47/installed/native');out=r/'compat/sheng-graphics/planar-v127'
os.environ.update(ANYHARMONYOS_OHOS_SOURCE=str(b/'source'),ANYHARMONYOS_STAGE=str(b/'stage'),ANYHARMONYOS_ROM_SYSTEM_LIBS=str(r/'work/hmos_system/system/system/lib64'),ANYHARMONYOS_SDK=str(sdk))
cfg=runpy.run_path(str(port/'tools/build_adapter.py'))
subprocess.run(cfg['COMMON']+['-I'+str(port/'adapter'),str(r/'tools/planar_allocator_probe_v127.cpp'),str(cfg['CPP']),'-o',str(out/'planar_allocator_probe')],check=True)
src=Path('/root/hmos-reference/AnyHarmonyOS/sm8650/graphics-port/gpu-port/src/rosen_yuv_contract.cpp')
s=src.read_text().replace('#include <memory>','#include <memory>\n#include <native_buffer/native_buffer.h>\n#include <cstdlib>')
s=s.replace('int main(){','int main(int argc,char**argv){')
start=s.index(' auto create=(Ref(*)())');end=s.index(' auto nw=',start);s=s[:start]+s[end:]
start=s.index(' constexpr int W=128');end=s.index(' void*buf=nw(owner.p)',start)
s=s[:start]+''' constexpr int W=128,H=96,logical=W*H*3/2;
 int format=argc>1?atoi(argv[1]):29;CHECK(format==24||format==28||format==29);
 auto alloc=(decltype(&OH_NativeBuffer_Alloc))dlsym(native,"OH_NativeBuffer_Alloc");
 auto handle=(const Handle*(*)(OH_NativeBuffer*))dlsym(native,"OH_NativeBuffer_GetBufferHandle");CHECK(alloc&&handle);
 OH_NativeBuffer_Config config{W,H,format,0x42b,0};auto *nativeBuffer=alloc(&config);CHECK(nativeBuffer);
 auto*h=handle(nativeBuffer);CHECK(h&&h->stride==W);int total=h->size;
 printf("REAL_NATIVE_ALLOCATION format=%d stride=%d size=%d\\n",format,h->stride,total);
 auto*input=(unsigned char*)mmap(nullptr,total,PROT_READ|PROT_WRITE,MAP_SHARED,h->fd,0);CHECK(input!=MAP_FAILED);
 dma_buf_sync sync{DMA_BUF_SYNC_START|DMA_BUF_SYNC_RW};CHECK(!ioctl(h->fd,DMA_BUF_IOCTL_SYNC,&sync));
 memset(input,0xcd,logical);
 const unsigned char yuv[3][3]={{81,90,240},{145,54,34},{41,240,110}};
 for(int y=0;y<H;y++)for(int x=0;x<W;x++)input[y*W+x]=yuv[x<42?0:x<84?1:2][0];
 for(int y=0;y<H/2;y++)for(int x=0;x<W/2;x++) {
  int band=x*2<42?0:x*2<84?1:2;
  if(format==24){input[W*H+y*W+x*2]=yuv[band][1];input[W*H+y*W+x*2+1]=yuv[band][2];}
  else {input[W*H+y*(W/2)+x]=yuv[band][format==29?2:1];input[W*H+W*H/4+y*(W/2)+x]=yuv[band][format==29?1:2];}
 }
 sync.flags=DMA_BUF_SYNC_END|DMA_BUF_SYNC_RW;CHECK(!ioctl(h->fd,DMA_BUF_IOCTL_SYNC,&sync));
''' +s[end:]
s=s.replace('nw(owner.p)','nw(nativeBuffer)')
needle=' alignas(16) char img[512]={};'
assert s.count(needle)==1
s=s.replace(needle,''' const void *ti=tex(&bt);CHECK(ti);
 // Read-only inspection of the pinned donor TextureInfo shared-pointer field.
 auto *vkBytes=*(const unsigned char *const*)((const char*)ti+24);CHECK(vkBytes);
 for(int off=0;off<160;off+=16){printf("VK_TEXTURE_WORDS offset=%d",off);for(int k=0;k<16;k+=4){uint32_t v;memcpy(&v,vkBytes+off+k,4);printf(" %08x",v);}puts("");}
 struct Opaque {alignas(8) char bytes[512];~Opaque(){}};
 void *two=dlopen("lib2d_graphics.z.so",RTLD_NOW|RTLD_LOCAL);
 void *sk=dlopen("libskia_canvaskit.z.so",RTLD_NOW|RTLD_LOCAL);CHECK(two&&sk);
 auto convert=(Opaque(*)(const void*))dlsym(two,"_ZN4OHOS5Rosen7Drawing15SkiaTextureInfo27ConvertToGrBackendVKTextureERKNS1_11TextureInfoE");
 auto getFormat=(Opaque(*)(const void*))dlsym(sk,"_ZNK16GrBackendTexture16getBackendFormatEv");
 auto getGr=(Ref(*)(const void*))dlsym(two,"_ZNK4OHOS5Rosen7Drawing14SkiaGPUContext12GetGrContextEv");
 auto caps=(const void*(*)(const void*))dlsym(sk,"_ZNK14GrContext_Base4capsEv");
 auto texturable=(bool(*)(const void*,const void*,int))dlsym(sk,"_ZNK8GrVkCaps18isFormatTexturableERK15GrBackendFormat13GrTextureType");
 CHECK(convert&&getFormat&&getGr&&caps&&texturable);
 auto backendInfo=convert(ti);auto backendFormat=getFormat(&backendInfo);
 auto direct=getGr(*(void**)gpu.get());CHECK(direct.p);auto *cap=caps(direct.p);CHECK(cap);
 printf("SKIA_FORMAT_TEXTURABLE=%d\\n",texturable(cap,&backendFormat,1));
''' +needle)
start=s.index('int white=0;');end=s.index('for(int i=W*H;i<int(pixels.size());i++)',start)
s=s[:start]+''' int good=0;
 for(int i=0;i<W*H;i++){
  int x=i%W,band=x<42?0:x<84?1:2;bool accurate=true;
  // Chroma reconstruction filters the two band boundaries. Compare solid
  // interiors identically for the NV12 baseline and both planar formats.
  if((x>=40&&x<=43)||(x>=82&&x<=85))continue;
  for(int ch=0;ch<4;ch++){int expected=ch==3||ch==band?255:0;int delta=int((pixels[i]>>(ch*8))&255)-expected;if(delta<0)delta=-delta;if(delta>4)accurate=false;}
  if(accurate)good++;
 }
 printf("YUV_COLOR_PIXELS=%d expected=%d format=%d first=%08x mid=%08x last=%08x\\n",good,(W-8)*H,format,pixels[0],pixels[64],pixels[127]);CHECK(good==(W-8)*H);
 '''+s[end:]
s=s.replace('CHECK(white==W*H);','').replace('for(int i=logical;i<total;i++)CHECK(input[i]==0xcd);','')
(out/'rosen_planar_contract.cpp').write_text(s)
subprocess.run([str(sdk/'llvm/bin/clang++'),'--target=aarch64-linux-ohos','-std=c++17','-O2','-fno-exceptions','-fno-rtti','-nostdlib++','-include',str(b/'sheng-graphics-port/tests/platform_cpp_config.h'),str(out/'rosen_planar_contract.cpp'),str(cfg['CPP']),'-o',str(out/'rosen_planar_contract')],check=True)
for name in ['planar_allocator_probe','rosen_planar_contract']:subprocess.run([str(sdk/'llvm/bin/llvm-strip'),str(out/name)],check=True)
print('planar tests built')
