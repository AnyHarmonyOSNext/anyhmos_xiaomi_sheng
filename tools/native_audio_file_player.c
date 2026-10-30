/* SPDX-License-Identifier: MIT - bounded original native AVPlayer file playback. */
#include <multimedia/player_framework/avplayer.h>
#include <stdio.h>
#include <unistd.h>
#include <fcntl.h>
#include <sys/stat.h>
#include <signal.h>
#include <stdlib.h>

static int state=AV_IDLE,failed,done;
static volatile sig_atomic_t interrupted;
static void stop_signal(int sig) { (void)sig; interrupted=1; }
static void info(OH_AVPlayer *p,AVPlayerOnInfoType type,int32_t extra)
{
    (void)p;
    if(type==AV_INFO_TYPE_STATE_CHANGE) {
        __atomic_store_n(&state,extra,__ATOMIC_RELEASE);
        printf("FILE_PLAYER_STATE=%d\n",extra);
    }
    if(type==AV_INFO_TYPE_EOS) __atomic_store_n(&done,1,__ATOMIC_RELEASE);
}
static void error(OH_AVPlayer *p,int32_t code,const char *message)
{
    (void)p; printf("FILE_PLAYER_ERROR=%d:%s\n",code,message?message:"");
    __atomic_store_n(&failed,1,__ATOMIC_RELEASE);
}
#define CHECK(x) do {int code=(x);printf("FILE_PLAYER_%s_RC=%d\n",#x,code);if(code){result=2;goto cleanup;}}while(0)
int main(int argc,char **argv)
{
    if(argc!=2) return 1;
    setbuf(stdout,0); setbuf(stderr,0); alarm(65);
    signal(SIGTERM,stop_signal);signal(SIGINT,stop_signal);
    int fd=open(argv[1],O_RDONLY|O_CLOEXEC|O_NOFOLLOW); struct stat st;
    if(fd<0 || fstat(fd,&st) || !S_ISREG(st.st_mode)) {perror("audio file");return 1;}
    int result=0; OH_AVPlayer *p=OH_AVPlayer_Create();
    if(!p){printf("FILE_PLAYER_CREATE_NULL\n");close(fd);return 2;}
    AVPlayerCallback cb={.onInfo=info,.onError=error};
    CHECK(OH_AVPlayer_SetPlayerCallback(p,cb));
    CHECK(OH_AVPlayer_SetFDSource(p,fd,0,st.st_size));
    CHECK(OH_AVPlayer_Prepare(p));
    for(int i=0;i<150 && !interrupted && !__atomic_load_n(&failed,__ATOMIC_ACQUIRE) &&
        __atomic_load_n(&state,__ATOMIC_ACQUIRE)!=AV_PREPARED;i++) usleep(100000);
    if(interrupted || failed || state!=AV_PREPARED){printf("FILE_PLAYER_PREPARE_INCOMPLETE=%d\n",state);result=3;goto cleanup;}
    CHECK(OH_AVPlayer_SetVolume(p,0.25f,0.25f));
    CHECK(OH_AVPlayer_Play(p));
    for(int i=0;i<350 && !interrupted && !__atomic_load_n(&failed,__ATOMIC_ACQUIRE) &&
        !__atomic_load_n(&done,__ATOMIC_ACQUIRE);i++) {
        usleep(100000);
        if(i%50==49) {int32_t ms=0;int rc=OH_AVPlayer_GetCurrentTime(p,&ms);printf("FILE_PLAYER_POSITION rc=%d ms=%d\n",rc,ms);}
    }
    if(failed) result=4;
    CHECK(OH_AVPlayer_Stop(p));
cleanup:
    printf("FILE_PLAYER_RELEASE_RC=%d\n",OH_AVPlayer_ReleaseSync(p));
    close(fd); printf("FILE_PLAYER_EXIT=%d\n",result); return result;
}
