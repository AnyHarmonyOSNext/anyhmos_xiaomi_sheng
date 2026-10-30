"""Keep the donor's complete IPCObjectStub ABI for the callback receiver."""
from pathlib import Path
r=Path(__file__).resolve().parents[1]
s=(r/'tools/native_screenlock_request_v4.cpp').read_text(encoding='utf-8')
s=s.replace('#include "screenlock_callback_stub.h"', '''#include "screenlock_callback_interface.h"
#include "iremote_object.h"
#include <dlfcn.h>
#include <new>
#include <cstdint>''')
start=s.index('class Callback final')
end=s.index('static void crash(',start)
s=s[:start]+'''static std::atomic<int>* callbackResult;
static int receive(void*,uint32_t code,MessageParcel& data,MessageParcel&,MessageOption&)
{
    if(data.ReadInterfaceToken()!=ScreenLockCallbackInterface::GetDescriptor())return E_SCREENLOCK_TRANSACT_ERROR;
    if(code!=ScreenLockCallbackInterface::ON_CALLBACK)return -1;
    int value=data.ReadInt32();
    if(callbackResult)callbackResult->store(value);
    std::printf("SCREENLOCK_CALLBACK_RECEIVED result=%d\\n",value);
    return 0;
}
static sptr<IRemoteObject> makeOriginalRemote()
{
    void* lib=dlopen("libipc_single.z.so",RTLD_NOW|RTLD_LOCAL);
    if(!lib)return nullptr;
    auto ctor=reinterpret_cast<void(*)(void*,std::u16string,bool)>(dlsym(lib,
        "_ZN4OHOS13IPCObjectStubC1ENSt3__h12basic_stringIDsNS1_11char_traitsIDsEENS1_9allocatorIDsEEEEb"));
    void* originalRequest=dlsym(lib,"_ZN4OHOS13IPCObjectStub15OnRemoteRequestEjRNS_13MessageParcelES2_RNS_13MessageOptionE");
    auto* send=reinterpret_cast<const uint32_t*>(dlsym(lib,
        "_ZN4OHOS13IPCObjectStub16SendRequestInnerEjRNS_13MessageParcelES2_RNS_13MessageOptionE"));
    // Pinned donor dispatch: ldr x8,[x8,#200], immediately before blr x8.
    if(!ctor||!originalRequest||!send||send[0x98/4]!=0xf9406508||send[0x9c/4]!=0xd63f0100){
        std::puts("SCREENLOCK_DONOR_ABI_GUARD_FAILED");return nullptr;
    }
    // Opaque storage deliberately exceeds the inspected complete constructor's
    // object (Parcelable at120, RefBase at136). No header-defined fields are read.
    void* object=::operator new(4096);
    ctor(object,ScreenLockCallbackInterface::GetDescriptor(),false);
    auto** table=*reinterpret_cast<void***>(object);
    if(table[200/8]!=originalRequest){std::puts("SCREENLOCK_DONOR_VTABLE_GUARD_FAILED");return nullptr;}
    // Original complete ctor uses table+32 for the primary vptr and+416 for
    // its next secondary vptr. Preserve that entire primary block/prefix.
    alignas(16) static uintptr_t privateTable[52];
    std::memcpy(privateTable,reinterpret_cast<const char*>(table)-32,sizeof(privateTable));
    privateTable[4+200/8]=reinterpret_cast<uintptr_t>(&receive);
    *reinterpret_cast<void***>(object)=reinterpret_cast<void**>(privateTable+4);
    std::puts("SCREENLOCK_ORIGINAL_STUB_READY private_dispatch_slot=200 original_library_untouched=1");
    return sptr<IRemoteObject>(reinterpret_cast<IRemoteObject*>(object));
}
class Callback final : public ScreenLockCallbackInterface {
    sptr<IRemoteObject> remote_;
public:
    std::atomic<int> result{-999};
    Callback():remote_(makeOriginalRemote()){callbackResult=&result;}
    sptr<IRemoteObject> AsObject() override {return remote_;}
    void OnCallBack(int32_t value) override {result.store(value);}
    bool Ready() const {return remote_!=nullptr;}
};
''' + s[end:]
s=s.replace('    sptr<Callback> callback = new Callback;', '    sptr<Callback> callback = new Callback;\n    if(!callback->Ready())return 11;')
(r/'tools/native_screenlock_request_v5.cpp').write_text(s,encoding='utf-8',newline='\n')
s=(r/'tools/build_screenlock_request_v4.py').read_text(encoding='utf-8').replace('v4','v5')
(r/'tools/build_screenlock_request_v5.py').write_text(s,encoding='utf-8',newline='\n')
print('v5 original-donor callback receiver source staged')
