#include <cstdio>
#include <cstring>
#include <string>
#include <vector>
#include <dlfcn.h>
#include <unistd.h>
#include "v4_0/iuser_auth_interface.h"
#include "idm_database.h"
#ifdef USERIAM_WIRE
#include <object_collector.h>
#include "v4_0/user_auth_interface_proxy.h"
#endif
namespace UA = OHOS::HDI::UserAuth::V4_0;
#define CHECK(x) do { if (!(x)) { printf("FAIL line=%d expression=%s\n",__LINE__,#x); return 1; } } while(0)
int main(int argc,char **argv) {
 setbuf(stdout,nullptr); alarm(25);
 void *lib=dlopen("libuser_auth_interface_service_4.0.z.so",RTLD_NOW);if(!lib){printf("DLOPEN %s\n",dlerror());return 2;}
 auto factory=reinterpret_cast<UA::IUserAuthInterface *(*)()>(dlsym(lib,"UserAuthInterfaceImplGetInstance"));CHECK(factory);
 OHOS::sptr<UA::IUserAuthInterface> api=factory();CHECK(api!=nullptr);
#ifdef USERIAM_WIRE
 void *driver=dlopen("libuser_auth_driver.z.so",RTLD_NOW);if(!driver){printf("DRIVER %s\n",dlerror());return 3;}
 printf("WIRE original factory loaded\n");
 OHOS::sptr<OHOS::HDI::HdiBase> base=api;
 OHOS::sptr<OHOS::IRemoteObject> remote=OHOS::HDI::ObjectCollector::GetInstance().GetOrNewObject(base,UA::IUserAuthInterface::GetDescriptor());CHECK(remote!=nullptr);
 printf("WIRE original stub factory succeeded\n");
 const std::string wireUdid(64,'a');
 CHECK(UA::UserAuthInterfaceProxy::Init_(wireUdid,remote)==0);
 std::vector<UA::CredentialInfo> wireCreds;CHECK(UA::UserAuthInterfaceProxy::GetCredential_(100,1,wireCreds,remote)==0&&wireCreds.size()==1);
 std::vector<UA::UserInfo> wireUsers;CHECK(UA::UserAuthInterfaceProxy::GetAllUserInfo_(wireUsers,remote)==0&&wireUsers.size()==1&&wireUsers[0].secureUid!=0);
 std::vector<UA::ExtUserInfo> wireExt;CHECK(UA::UserAuthInterfaceProxy::GetAllExtUserInfo_(wireExt,remote)==0&&wireExt.size()==1&&wireExt[0].userId==100&&wireExt[0].userInfo.secureUid==wireUsers[0].secureUid);
 std::vector<uint8_t> wireChallenge;CHECK(UA::UserAuthInterfaceProxy::OpenSession_(100,wireChallenge,remote)==0&&wireChallenge.size()==32);CHECK(UA::UserAuthInterfaceProxy::CloseSession_(100,remote)==0);
 UA::UserAuthTokenPlain wireToken={};std::vector<uint8_t> wireSecret;
 CHECK(UA::UserAuthInterfaceProxy::VerifyAuthToken_(std::vector<uint8_t>(32,0xa5),1000,wireToken,wireSecret,remote)!=0&&wireSecret.empty());
 printf("USERIAM_CONTRACT_RESULT=0 phase=wire original proxy/stub serialization and token rejection\n");return 0;
#endif
 const std::string udid(64,'a');
 if(argc>1&&!strcmp(argv[1],"corrupt")){
  CHECK(api->Init(udid)!=0);std::vector<UA::CredentialInfo> rows;CHECK(api->GetCredential(100,1,rows)!=0);
  printf("USERIAM_CONTRACT_RESULT=0 phase=corrupt initialization and query fail closed\n");return 0;
 }
 CHECK(api->Init(udid)==0);
 uint32_t major=0,minor=0;CHECK(api->GetVersion(major,minor)==0&&major==4&&minor==0);
 std::vector<UA::CredentialInfo> credentials;CHECK(api->GetCredential(100,1,credentials)==0);
 uint64_t expectedCredential=0;
 bool persisted=argc>1&&!strcmp(argv[1],"persisted");
 if(!persisted){
  CHECK(credentials.empty());
  std::vector<UA::UserInfo> users;CHECK(api->GetAllUserInfo(users)==0&&users.empty());
  printf("PASS empty database returns zero credentials and zero users\n");
  std::vector<uint8_t> first,second;CHECK(api->OpenSession(100,first)==0);CHECK(api->CloseSession(100)==0);CHECK(api->OpenSession(100,second)==0);CHECK(api->CloseSession(100)==0);CHECK(first.size()==32&&second.size()==32&&first!=second);
  printf("PASS independent enrollment challenges\n");
  auto add=reinterpret_cast<ResultCode (*)(int32_t,CredentialInfoHal*,int32_t)>(dlsym(lib,"AddCredentialInfo"));CHECK(add);
  CredentialInfoHal fixture={};fixture.credentialId=0x10203040;fixture.templateId=0x50607080;fixture.authType=1;fixture.executorSensorHint=1;fixture.executorMatcher=1;fixture.capabilityLevel=1;
  CHECK(add(100,&fixture,0)==0);
  expectedCredential=fixture.credentialId;CHECK(expectedCredential!=0);
  FILE *record=fopen("/data/test/expected-credential","wb");CHECK(record);CHECK(fwrite(&expectedCredential,sizeof(expectedCredential),1,record)==1);CHECK(fclose(record)==0);
  CHECK(api->Init(udid)==0);credentials.clear();CHECK(api->GetCredential(100,1,credentials)==0);
 }
 if(persisted){FILE *record=fopen("/data/test/expected-credential","rb");CHECK(record);CHECK(fread(&expectedCredential,sizeof(expectedCredential),1,record)==1);fclose(record);}
 CHECK(credentials.size()==1&&credentials[0].credentialId==expectedCredential);
 std::vector<UA::UserInfo> users;std::vector<UA::ExtUserInfo> ext;
 CHECK(api->GetAllUserInfo(users)==0&&users.size()==1);CHECK(api->GetAllExtUserInfo(ext)==0&&ext.size()==1&&ext[0].userId==100);CHECK(users[0].secureUid!=0&&users[0].secureUid==ext[0].userInfo.secureUid);
 CHECK(!users[0].enrolledInfos.empty());
 printf("PASS persisted credential query and genuine user enumeration\n");
 UA::UserAuthTokenPlain token={};std::vector<uint8_t> secret;
 for(size_t length:{size_t(0),size_t(1),size_t(32),size_t(512)}){std::vector<uint8_t> forged(length,0xa5);int rc=api->VerifyAuthToken(forged,1000,token,secret);CHECK(rc!=0);CHECK(secret.empty());}
 UA::CredentialOperateResult removed={};CHECK(api->DeleteCredential(100,expectedCredential,{},removed)!=0);
 credentials.clear();CHECK(api->GetCredential(100,1,credentials)==0&&credentials.size()==1);
 printf("PASS forged tokens rejected and unauthenticated credential deletion rejected\n");
 printf("USERIAM_CONTRACT_RESULT=0 phase=%s\n",persisted?"persisted":"fresh");
 return 0;
}
