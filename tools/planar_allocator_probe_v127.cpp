#include "idisplay_buffer_vdi.h"
#include <cstdio>
#include <cstring>
#include <dlfcn.h>
#include <unistd.h>
using namespace OHOS::HDI::Display::Buffer::V1_0;
#define CHECK(x) do { if(!(x)) { printf("FAIL %d %s\n",__LINE__,#x);return 1; } } while(0)
int main(int argc,char **argv) {
 setbuf(stdout,nullptr);alarm(15);CHECK(argc==2);
 void *lib=dlopen(argv[1],RTLD_NOW|RTLD_LOCAL);CHECK(lib);
 auto create=(CreateDisplayBufferVdiFunc)dlsym(lib,"CreateDisplayBufferVdi");
 auto destroy=(DestroyDisplayBufferVdiFunc)dlsym(lib,"DestroyDisplayBufferVdi");CHECK(create&&destroy);
 auto *v=create();CHECK(v);
 for(uint32_t format: {24u,25u,28u,29u}) {
  BufferHandle *h=nullptr; CHECK(!v->AllocMem({720,1280,0x409,format,0},h)&&h);
  CHECK(h->stride==768 && h->size==1478656 && h->width==720 && h->height==1280);
  OHOS::HDI::Display::Buffer::V1_2::ImageLayout layout;
  CHECK(!v->GetImageLayout(*h,layout));
  CHECK(layout.planes.size()==(format>=28?3u:2u));
  auto *p=(unsigned char*)v->Mmap(*h);CHECK(p); CHECK(!v->InvalidateCache(*h));
  memset(p,0x51,983040);
  if(format>=28) {
   CHECK(layout.planes[1].offset==983040 && layout.planes[1].hStride==384);
   CHECK(layout.planes[2].offset==1228800 && layout.planes[2].hStride==384);
   memset(p+983040,format==29?0xe0:0x60,245760);
   memset(p+1228800,format==29?0x60:0xe0,245760);
  }
  CHECK(!v->FlushCache(*h));CHECK(!v->Unmap(*h));
  std::vector<uint8_t> color(16,1),got;
  CHECK(!v->SetMetadata(*h,1,color));CHECK(!v->GetMetadata(*h,1,got)&&got==color);
  BufferHandle imported=*h;imported.fd=dup(h->fd);imported.virAddr=nullptr;
  CHECK(imported.fd>=0 && !v->RegisterBuffer(imported));
  p=(unsigned char*)v->Mmap(imported);CHECK(p);CHECK(!v->InvalidateCache(imported));
  CHECK(p[0]==0x51 && p[983039]==0x51);
  if(format>=28) CHECK(p[983040]==(format==29?0xe0:0x60) && p[1228800]==(format==29?0x60:0xe0));
  CHECK(!v->FlushCache(imported));CHECK(!v->Unmap(imported));close(imported.fd);
  printf("PLANAR_ALLOC_PASS format=%u planes=%zu stride=%d size=%d\n",format,layout.planes.size(),h->stride,h->size);
  v->FreeMem(*h);
 }
 BufferHandle *h=nullptr; CHECK(v->AllocMem({721,1280,0x409,29,0},h)!=0 && !h);
 CHECK(v->AllocMem({720,1280,0x809,29,0},h)!=0 && !h);
 CHECK(v->AllocMem({720,1280,0x409,999,0},h)!=0 && !h);
 destroy(v); puts("PLANAR_ALLOC_CONTRACT=0 legacy_nv12_nv21=1 bounds=1 protected_rejected=1");
}
