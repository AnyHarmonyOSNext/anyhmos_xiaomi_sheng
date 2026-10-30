/* Read-only supplicant diagnostics; never print saved networks or credentials. */
#define _GNU_SOURCE
#include <sys/socket.h>
#include <sys/un.h>
#include <sys/time.h>
#include <unistd.h>
#include <stdio.h>
#include <string.h>
#include <stddef.h>
#include <stdlib.h>

int main(void)
{
    setvbuf(stdout,NULL,_IOLBF,0); alarm(15);
    int fd=socket(AF_UNIX,SOCK_DGRAM|SOCK_CLOEXEC,0);
    if(fd<0)return 2;
    struct sockaddr_un local={.sun_family=AF_UNIX},peer={.sun_family=AF_UNIX};
    snprintf(local.sun_path,sizeof(local.sun_path),"/data/local/tmp/wpa-ro-%ld.sock",(long)getpid());
    strcpy(peer.sun_path,"/data/service/el1/public/wifi/sockets/wpa/wlan0");
    if(bind(fd,(void*)&local,sizeof(local))<0){perror("bind");return 3;}
    int result=0;
    if(connect(fd,(void*)&peer,sizeof(peer))<0){perror("connect");result=4;goto done;}
    struct timeval tv={.tv_sec=3};
    setsockopt(fd,SOL_SOCKET,SO_RCVTIMEO,&tv,sizeof(tv));
    const char*commands[]={"STATUS","SIGNAL_POLL","GET_CAPABILITY modes"};
    for(unsigned i=0;i<sizeof(commands)/sizeof(commands[0]);++i){
        if(send(fd,commands[i],strlen(commands[i]),0)<0){result=5;break;}
        char buf[8192];ssize_t n=recv(fd,buf,sizeof(buf)-1,0);
        if(n<0){perror("recv");result=6;break;}
        buf[n]=0;printf("WPA_READONLY %s\n",commands[i]);
        if(i){fputs(buf,stdout);continue;}
        char*save=NULL;
        for(char*p=strtok_r(buf,"\n",&save);p;p=strtok_r(NULL,"\n",&save)){
            const char*keys[]={"wpa_state=","freq=","wifi_generation=","key_mgmt=","pairwise_cipher=","group_cipher="};
            for(unsigned k=0;k<sizeof(keys)/sizeof(keys[0]);++k)
                if(strncmp(p,keys[k],strlen(keys[k]))==0)puts(p);
        }
    }
done:
    close(fd);unlink(local.sun_path);return result;
}
