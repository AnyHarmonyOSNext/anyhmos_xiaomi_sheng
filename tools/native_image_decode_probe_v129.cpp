/* Original donor public NDK image decoder; read-only source, isolated output. */
#include <multimedia/image_framework/image/image_source_native.h>
#include <multimedia/image_framework/image/pixelmap_native.h>
#include <dlfcn.h>
#include <fcntl.h>
#include <inttypes.h>
#include <stdio.h>
#include <stdlib.h>
#include <time.h>
#include <unistd.h>
#define API(n) static __typeof__(&n) p_##n
API(OH_ImageSourceNative_CreateFromFd);
API(OH_ImageSourceNative_CreatePixelmap);
API(OH_ImageSourceNative_Release);
API(OH_DecodingOptions_Create);
API(OH_DecodingOptions_SetPixelFormat);
API(OH_DecodingOptions_Release);
API(OH_PixelmapImageInfo_Create);
API(OH_PixelmapImageInfo_GetWidth);
API(OH_PixelmapImageInfo_GetHeight);
API(OH_PixelmapImageInfo_GetRowStride);
API(OH_PixelmapImageInfo_GetPixelFormat);
API(OH_PixelmapImageInfo_Release);
API(OH_PixelmapNative_GetImageInfo);
API(OH_PixelmapNative_ReadPixels);
API(OH_PixelmapNative_Release);
#define LOAD(lib,n) do { p_##n = (__typeof__(p_##n))dlsym(lib,#n); if(!p_##n) { printf("MISSING %s %s\n",#n,dlerror()); return 3; } } while(0)
#define CHECK(n) do { int rc=(n); if(rc) { printf("DECODE_FAIL line=%d rc=%d\n",__LINE__,rc); return 4; } } while(0)
static uint64_t now_ns(void) { struct timespec t; clock_gettime(CLOCK_MONOTONIC,&t); return (uint64_t)t.tv_sec*1000000000+t.tv_nsec; }
int main(int argc,char **argv) {
    setbuf(stdout,NULL); alarm(20); if(argc!=3) return 2;
    void *s=dlopen("libimage_source.so",RTLD_NOW|RTLD_LOCAL);
    void *p=dlopen("libpixelmap.so",RTLD_NOW|RTLD_LOCAL);
    if(!s||!p) {printf("DLOPEN_FAIL %s\n",dlerror());return 3;}
    LOAD(s,OH_ImageSourceNative_CreateFromFd); LOAD(s,OH_ImageSourceNative_CreatePixelmap);
    LOAD(s,OH_ImageSourceNative_Release); LOAD(s,OH_DecodingOptions_Create);
    LOAD(s,OH_DecodingOptions_SetPixelFormat); LOAD(s,OH_DecodingOptions_Release);
    LOAD(p,OH_PixelmapImageInfo_Create); LOAD(p,OH_PixelmapImageInfo_GetWidth);
    LOAD(p,OH_PixelmapImageInfo_GetHeight); LOAD(p,OH_PixelmapImageInfo_GetRowStride);
    LOAD(p,OH_PixelmapImageInfo_GetPixelFormat); LOAD(p,OH_PixelmapImageInfo_Release);
    LOAD(p,OH_PixelmapNative_GetImageInfo); LOAD(p,OH_PixelmapNative_ReadPixels);
    LOAD(p,OH_PixelmapNative_Release);
    int fd=open(argv[1],O_RDONLY|O_CLOEXEC); if(fd<0)return 3;
    uint64_t begin=now_ns(); OH_ImageSourceNative *source=NULL; OH_DecodingOptions *opt=NULL;
    OH_PixelmapNative *map=NULL; OH_Pixelmap_ImageInfo *info=NULL;
    CHECK(p_OH_ImageSourceNative_CreateFromFd(fd,&source));
    CHECK(p_OH_DecodingOptions_Create(&opt));
    CHECK(p_OH_DecodingOptions_SetPixelFormat(opt,PIXEL_FORMAT_RGBA_8888));
    CHECK(p_OH_ImageSourceNative_CreatePixelmap(source,opt,&map));
    CHECK(p_OH_PixelmapImageInfo_Create(&info));
    CHECK(p_OH_PixelmapNative_GetImageInfo(map,info));
    uint32_t w=0,h=0,stride=0;int32_t format=0;
    CHECK(p_OH_PixelmapImageInfo_GetWidth(info,&w)); CHECK(p_OH_PixelmapImageInfo_GetHeight(info,&h));
    CHECK(p_OH_PixelmapImageInfo_GetRowStride(info,&stride));
    CHECK(p_OH_PixelmapImageInfo_GetPixelFormat(info,&format));
    if(!w||!h||w>16384||h>16384||stride<w*4||format!=PIXEL_FORMAT_RGBA_8888)return 5;
    size_t size=(size_t)stride*h; if(size>128*1024*1024)return 5;
    unsigned char *pixels=(unsigned char *)calloc(1,size);if(!pixels)return 5;
    CHECK(p_OH_PixelmapNative_ReadPixels(map,pixels,&size));
    int out=open(argv[2],O_WRONLY|O_CREAT|O_EXCL|O_CLOEXEC,0600);if(out<0)return 6;
    uint64_t hash=UINT64_C(14695981039346656037);size_t bytes=0;
    for(uint32_t y=0;y<h;y++) {
        const unsigned char *row=pixels+(size_t)y*stride;
        for(size_t x=0;x<(size_t)w*4;x++){hash^=row[x];hash*=UINT64_C(1099511628211);}
        size_t offset=0;while(offset<(size_t)w*4) {
            ssize_t n=write(out,row+offset,(size_t)w*4-offset);if(n<=0)return 6;offset+=n;bytes+=n;
        }
    }
    close(out);
    printf("IMAGE_DECODE_PASS width=%u height=%u stride=%u format=%d packed_bytes=%zu fnv1a64=%016" PRIx64 " elapsed_ms=%.3f\n",w,h,stride,format,bytes,hash,(now_ns()-begin)/1e6);
    free(pixels);CHECK(p_OH_PixelmapImageInfo_Release(info)); CHECK(p_OH_PixelmapNative_Release(map));
    CHECK(p_OH_DecodingOptions_Release(opt));CHECK(p_OH_ImageSourceNative_Release(source));close(fd);
    return 0;
}
