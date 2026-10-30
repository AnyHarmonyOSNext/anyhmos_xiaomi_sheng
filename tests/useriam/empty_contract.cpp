// Check the inherited 4.1 ABI using original proxy/stub marshalling, without
// enrolling credentials or changing account verification/lockscreen state.
#include "user_auth/v4_1/iuser_auth_interface.h"
#include "user_auth/v4_1/user_auth_interface_proxy.h"
#include <object_collector.h>
#include <dlfcn.h>
#include <cstdio>
#include <unistd.h>
namespace UA=OHOS::HDI::UserAuth::V4_1;
namespace B=OHOS::HDI::UserAuth::V4_0;
#define CHECK(x) do{if(!(x)){printf("USERIAM_EMPTY_FAIL line=%d expr=%s\n",__LINE__,#x);return 1;}}while(0)
int main(){
 setbuf(stdout,nullptr);alarm(20);
 void *lib=dlopen("/compat/lib64/libuser_auth_interface_service_4.1.z.so",RTLD_NOW);if(!lib){puts(dlerror());return 2;}
 auto factory=reinterpret_cast<UA::IUserAuthInterface*(*)()>(dlsym(lib,"UserAuthInterfaceImplGetInstance"));CHECK(factory);
 OHOS::sptr<UA::IUserAuthInterface> api=factory();CHECK(api!=nullptr);
 uint32_t major=0,minor=0;CHECK(api->GetVersion(major,minor)==0&&major==4&&minor==1);
 CHECK(api->Init(std::string(64,'a'))==0);
 std::vector<B::CredentialInfo> credentials;CHECK(api->GetCredential(100,1,credentials)==0&&credentials.empty());
 printf("USERIAM_EMPTY_DIRECT_OK version=%u.%u credentials=%zu\n",major,minor,credentials.size());
 void *stub=dlopen("/vendor/lib64/libuser_auth_stub_4.1.z.so",RTLD_NOW);CHECK(stub);
 OHOS::sptr<OHOS::HDI::HdiBase> base=api;
 auto remote=OHOS::HDI::ObjectCollector::GetInstance().GetOrNewObject(base,UA::IUserAuthInterface::GetDescriptor());CHECK(remote!=nullptr);
 CHECK(B::UserAuthInterfaceProxy::GetCredential_(100,1,credentials,remote)==0&&credentials.empty());
 UA::AuthParamExt auth={};std::vector<B::ScheduleInfo> schedules;
 CHECK(UA::UserAuthInterfaceProxy::BeginAuthenticationExt_(1,auth,schedules,remote)!=0);
 B::UserAuthTokenPlain token={};std::vector<uint8_t> secret;
 CHECK(B::UserAuthInterfaceProxy::VerifyAuthToken_(std::vector<uint8_t>(32,0xa5),1000,token,secret,remote)!=0&&secret.empty());
 puts("USERIAM_EMPTY_WIRE_OK original_4.1_stub inherited_4.0_proxy extended_auth_and_invalid_token_rejected");
 return 0;
}
