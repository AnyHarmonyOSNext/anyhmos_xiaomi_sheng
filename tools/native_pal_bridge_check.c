/* Bounded real PCM transport validation from native OHOS to original Bionic. */
#include "pal_client.h"
#include <stdio.h>
#include <unistd.h>

static int request(int fd, unsigned op, unsigned arg0, unsigned arg1,
    const void *data, unsigned bytes)
{
    struct sheng_pal_reply r={0};
    int rc=sheng_pal_request(fd,op,arg0,arg1,data,bytes,&r);
    printf("PAL_BRIDGE op=%u rc=%d written=%u frames=%llu\n",op,rc,r.bytes,
        (unsigned long long)r.written_frames);
    if (rc || (op==SHENG_PAL_WRITE && r.bytes!=bytes)) return 1;
    return 0;
}

int main(void)
{
    setbuf(stdout,0); alarm(15);
    int fd=sheng_pal_connect();
    printf("PAL_BRIDGE_CONNECT=%d\n",fd);
    if (fd<0) return 2;
    int rc=request(fd,SHENG_PAL_OPEN,48000,2,0,0);
    if (!rc) rc=request(fd,SHENG_PAL_VOLUME,30000,0,0,0);
    if (!rc) rc=request(fd,SHENG_PAL_START,0,0,0,0);
    short silence[480]={0};
    for (int i=0;!rc && i<40;i++) rc=request(fd,SHENG_PAL_WRITE,0,0,silence,sizeof(silence));
    if (!rc) rc=request(fd,SHENG_PAL_VOLUME,0,0,0,0);
    int stop=request(fd,SHENG_PAL_STOP,0,0,0,0);
    int end=request(fd,SHENG_PAL_CLOSE,0,0,0,0);
    close(fd);
    printf("PAL_BRIDGE_CHECK_EXIT=%d\n",rc || stop || end);
    return rc || stop || end;
}
