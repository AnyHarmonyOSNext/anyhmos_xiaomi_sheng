// Run the actual donor delegates with only their imported crypto redirected.
#include <cstdint>
#include <cstdio>
#include <cstring>
#include <dlfcn.h>
#include <memory>
#include <string>
#include <vector>
#include <unistd.h>
namespace OHOS::NativeRdb {
struct RDBCryptoFault { int32_t code; std::string message; };
struct RDBCryptoParam { std::vector<uint8_t> nonce_,KeyValue; };
class RDBCrypto {
public:
 virtual ~RDBCrypto()=default;
 virtual int32_t Init(RDBCryptoFault &)=0;
 virtual bool RootKeyExists()=0;
 virtual std::vector<uint8_t> Encrypt(const RDBCryptoParam &,RDBCryptoFault &)=0;
 virtual std::vector<uint8_t> Decrypt(const RDBCryptoParam &,RDBCryptoFault &)=0;
};
}
namespace OHOS::DistributedKv {
struct KVDBCryptoParam { std::vector<uint8_t> keyValue,nonceValue; };
class KVDBCrypto {
public:
 virtual ~KVDBCrypto()=default;
 virtual bool CheckRootKey()=0;
 virtual bool GenerateRootKey()=0;
 virtual std::vector<uint8_t> Encrypt(const KVDBCryptoParam &)=0;
 virtual std::vector<uint8_t> Decrypt(const KVDBCryptoParam &)=0;
};
}
int main() {
 alarm(15);setbuf(stdout,nullptr);
 using namespace OHOS::NativeRdb;
 void *lib=dlopen("/data/local/tmp/db-test-rdb.so",RTLD_NOW|RTLD_LOCAL);
 if(!lib){printf("LOAD_ERROR %s\n",dlerror());return 2;}
 auto create=reinterpret_cast<std::shared_ptr<RDBCrypto>(*)(const std::vector<uint8_t>&)>(dlsym(lib,"CreateRdbCryptoDelegate"));
 if(!create)return 3;
 const char *a="DistributedDataRdb";
 auto object=create(std::vector<uint8_t>(a,a+strlen(a)));RDBCryptoFault fault{};
 int ret=object->Init(fault);printf("ORIGINAL_RDB_INIT ret=%d code=%d\n",ret,fault.code);if(ret)return 4;
 if(!object->RootKeyExists())return 5;
 RDBCryptoParam p;p.nonce_.assign(12,0x31);for(int i=0;i<128;i++)p.KeyValue.push_back(i^0x5a);
 auto cipher=object->Encrypt(p,fault);printf("ORIGINAL_RDB_ENCRYPT bytes=%zu code=%d\n",cipher.size(),fault.code);
 if(cipher.size()!=144)return 6;
 RDBCryptoParam q;q.nonce_=p.nonce_;q.KeyValue=cipher;
 auto plain=object->Decrypt(q,fault);if(plain!=p.KeyValue)return 7;
 q.KeyValue.back()^=1;
 auto bad=object->Decrypt(q,fault);if(!bad.empty())return 8;
 puts("ORIGINAL_RDB_DELEGATE_REAL_ENCRYPT_DECRYPT_BAD_TAG_REJECTED_OK");
 void *kvlib=dlopen("/data/local/tmp/db-test-kv.so",RTLD_NOW|RTLD_LOCAL);
 if(!kvlib){printf("KV_LOAD_ERROR %s\n",dlerror());return 9;}
 using namespace OHOS::DistributedKv;
 auto kvcreate=reinterpret_cast<std::shared_ptr<KVDBCrypto>(*)(const std::vector<uint8_t>&,const std::vector<uint8_t>)>(dlsym(kvlib,"CreateKvdbCryptoDelegate"));
 if(!kvcreate)return 10;
 a="distributeddb_client_root_key";
 auto kv=kvcreate(std::vector<uint8_t>(a,a+strlen(a)),std::vector<uint8_t>{1,2,3,4});
 if(!kv->GenerateRootKey()||!kv->CheckRootKey())return 11;
 KVDBCryptoParam kp;kp.keyValue=p.KeyValue;kp.nonceValue=p.nonce_;
 auto kc=kv->Encrypt(kp);printf("ORIGINAL_KV_ENCRYPT bytes=%zu\n",kc.size());if(kc.size()!=144)return 12;
 kp.keyValue=kc;if(kv->Decrypt(kp)!=p.KeyValue)return 13;
 kp.keyValue.back()^=1;if(!kv->Decrypt(kp).empty())return 14;
 puts("ORIGINAL_KV_DELEGATE_REAL_ENCRYPT_DECRYPT_BAD_TAG_REJECTED_OK");return 0;
}
