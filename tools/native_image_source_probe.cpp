// Read-only donor URI classification. No loader, cache or policy is changed.
#include <cstdio>
#include <dlfcn.h>
#include <string>
#include <unistd.h>
int main()
{
    alarm(12);
    void *lib = dlopen("libace_compatible.z.so", RTLD_NOW | RTLD_LOCAL);
    if (!lib) { std::fprintf(stderr, "IMAGE_SOURCE_DLOPEN %s\n", dlerror()); return 2; }
    auto resolve = reinterpret_cast<int (*)(const std::string &)>(dlsym(lib,
        "_ZN4OHOS3Ace15ImageSourceInfo14ResolveURITypeERKNSt3__h12basic_stringIcNS2_11char_traitsIcEENS2_9allocatorIcEEEE"));
    if (!resolve) return 3;
    for (const char *value : {"", "data:image/png;base64,AAAA", "data:image/sdr_astc_4x4;base64,AAAA",
                              "data:image/astc;base64,AAAA", "file:///data/local/tmp/icon.png",
                              "resource://RAWFILE/icon.png"}) {
        std::printf("IMAGE_SOURCE uri=%s type=%d\n", value, resolve(std::string(value)));
    }
    return 0;
}
