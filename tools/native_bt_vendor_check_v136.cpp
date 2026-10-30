#include <stddef.h>
#include "ohos_bt_vendor_lib.h"
#include <stdio.h>
#include <stdlib.h>
#include <dlfcn.h>
#include <unistd.h>
#include <poll.h>
#include <sys/socket.h>
static int callback_result=-1;
static void *allocate(int n){return n>0?malloc(static_cast<size_t>(n)):nullptr;}
static void completed(BtOpResultT result){callback_result=result;printf("BT_VENDOR_CALLBACK=%d\n",result);}
int main()
{
    setvbuf(stdout,nullptr,_IOLBF,0);alarm(35);
    void *lib=dlopen("/data/local/tmp/libbt_vendor_sheng_v136.so",RTLD_NOW|RTLD_LOCAL);
    if(!lib){printf("BT_VENDOR_LOAD_ERROR=%s\n",dlerror());return 11;}
    auto api=static_cast<const BtVendorInterfaceT *>(dlsym(lib,"BLUETOOTH_VENDOR_LIB_INTERFACE"));
    if(!api || api->size!=sizeof(*api))return 12;
    BtVendorCallbacksT cb={sizeof(cb),completed,allocate,free,nullptr};
    unsigned char address[6]{};
    int rc=api->init(&cb,address);printf("BT_VENDOR_INIT=%d\n",rc);if(rc)return 13;
    rc=api->op(BT_OP_POWER_ON,nullptr);printf("BT_VENDOR_REAL_POWER=%d\n",rc);if(rc){api->close();return 14;}
    int fds[HCI_MAX_CHANNEL]={-1,-1,-1,-1};rc=api->op(BT_OP_HCI_CHANNEL_OPEN,fds);
    printf("BT_VENDOR_H4_COUNT=%d fd=%d\n",rc,fds[0]);if(rc!=1){api->close();return 15;}
    rc=api->op(BT_OP_INIT,nullptr);if(rc || callback_result!=0){api->close();return 16;}
    unsigned char request[]={1,1,0x10,0};
    if(send(fds[0],request,sizeof(request),0)!=sizeof(request)){api->close();return 17;}
    unsigned char reply[258]{};size_t total=0,expected=3;
    while(total<expected){
        pollfd p={fds[0],POLLIN,0};if(poll(&p,1,3000)<=0){api->close();return 18;}
        ssize_t got=recv(fds[0],reply+total,expected-total,0);if(got<=0){api->close();return 19;}
        total+=got;if(total==3)expected=3+reply[2];
    }
    printf("BT_VENDOR_REAL_H4_REPLY=");for(size_t i=0;i<total;i++)printf("%02x",reply[i]);putchar('\n');
    bool ok=total>=7 && reply[0]==4 && reply[1]==0x0e && reply[4]==1 && reply[5]==0x10 && reply[6]==0;
    api->op(BT_OP_HCI_CHANNEL_CLOSE,nullptr);api->op(BT_OP_POWER_OFF,nullptr);api->close();
    printf("BT_VENDOR_REAL_H4_SUCCESS=%d\n",ok);return ok?0:20;
}
