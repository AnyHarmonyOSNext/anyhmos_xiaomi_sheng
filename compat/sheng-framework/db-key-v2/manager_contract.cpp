// Invoke the actual donor CryptoManager with its original ABI and machine code.
#include <cstddef>
#include <cstdint>
#include <cstdio>
#include <dlfcn.h>
#include <string>
#include <vector>
#include <unistd.h>
struct CryptoParams {
    int32_t area=1;
    std::string userId="0";
    std::vector<uint8_t> keyAlias,nonce;
};
static_assert(offsetof(CryptoParams,userId)==8);
static_assert(offsetof(CryptoParams,keyAlias)==32);
static_assert(offsetof(CryptoParams,nonce)==56);
int main(int argc,char **argv)
{
    alarm(15);setbuf(stdout,nullptr);
    if(argc!=2)return 2;
    void *lib=dlopen(argv[1],RTLD_NOW|RTLD_LOCAL);
    if(!lib){printf("MANAGER_LOAD_ERROR %s\n",dlerror());return 3;}
    auto instance=reinterpret_cast<void *(*)()>(dlsym(lib,"_ZN4OHOS15DistributedData13CryptoManager11GetInstanceEv"));
    auto generate=reinterpret_cast<int (*)(void *)>(dlsym(lib,"_ZN4OHOS15DistributedData13CryptoManager15GenerateRootKeyEv"));
    auto exists=reinterpret_cast<int (*)(void *)>(dlsym(lib,"_ZN4OHOS15DistributedData13CryptoManager12CheckRootKeyEv"));
    using Crypt=std::vector<uint8_t> (*)(void *,const std::vector<uint8_t> &,CryptoParams &);
    auto enc=reinterpret_cast<Crypt>(dlsym(lib,"_ZN4OHOS15DistributedData13CryptoManager7EncryptERKNSt3__h6vectorIhNS2_9allocatorIhEEEERNS1_12CryptoParamsE"));
    auto dec=reinterpret_cast<Crypt>(dlsym(lib,"_ZN4OHOS15DistributedData13CryptoManager7DecryptERKNSt3__h6vectorIhNS2_9allocatorIhEEEERNS1_12CryptoParamsE"));
    if(!instance||!generate||!exists||!enc||!dec)return 4;
    void *m=instance();
    if(generate(m)||exists(m))return 5;
    std::vector<uint8_t> plain(128);for(size_t i=0;i<plain.size();i++)plain[i]=static_cast<uint8_t>(i^0x39);
    CryptoParams p;auto cipher=enc(m,plain,p);
    printf("ORIGINAL_MANAGER_ENCRYPT bytes=%zu nonce=%zu\n",cipher.size(),p.nonce.size());
    if(cipher.size()!=144||p.nonce.size()!=12)return 6;
    auto result=dec(m,cipher,p);if(result!=plain)return 7;
    if(generate(m))return 8;
    result=dec(m,cipher,p);if(result!=plain)return 9;
    cipher.back()^=1;result=dec(m,cipher,p);if(!result.empty())return 10;
    puts("ORIGINAL_MANAGER_DE_KEY_WRAP_REUSE_AND_BAD_TAG_DENIAL_OK");
    return 0;
}
