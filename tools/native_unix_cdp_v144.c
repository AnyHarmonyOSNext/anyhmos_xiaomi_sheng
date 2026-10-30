/* Temporary local-only DevTools client; opens no listener or TCP connection. */
#define _GNU_SOURCE
#include <sys/socket.h>
#include <sys/un.h>
#include <sys/random.h>
#include <sys/time.h>
#include <unistd.h>
#include <stddef.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <errno.h>

static int exact(int fd, void *data, size_t n, int writing)
{
    unsigned char *p=data;
    while (n) {
        ssize_t r=writing ? send(fd,p,n,MSG_NOSIGNAL) : recv(fd,p,n,0);
        if (r<0 && errno==EINTR) continue;
        if (r<=0) return -1;
        p+=r;n-=(size_t)r;
    }
    return 0;
}
int main(int argc,char **argv)
{
    alarm(12);
    if (argc!=3 && argc!=5) return 2;
    /* Only the known abstract WebView diagnostic endpoint can be selected. */
    if (strncmp(argv[1],"webview_devtools_remote_",24) || strlen(argv[1])>95) return 3;
    int fd=socket(AF_UNIX,SOCK_STREAM|SOCK_CLOEXEC,0);
    if (fd<0) {perror("socket");return 4;}
    struct timeval tv={3,0};
    setsockopt(fd,SOL_SOCKET,SO_RCVTIMEO,&tv,sizeof(tv));
    setsockopt(fd,SOL_SOCKET,SO_SNDTIMEO,&tv,sizeof(tv));
    struct sockaddr_un a={.sun_family=AF_UNIX};
    memcpy(a.sun_path+1,argv[1],strlen(argv[1]));
    if(connect(fd,(void*)&a,offsetof(struct sockaddr_un,sun_path)+1+strlen(argv[1]))) {
        perror("connect");close(fd);return 5;
    }
    char request[1024];
    int ws=argc==5;
    if (argv[2][0]!='/' || strchr(argv[2],'\r') || strchr(argv[2],'\n')) return 6;
    int n=snprintf(request,sizeof(request),
        ws ? "GET %s HTTP/1.1\r\nHost: localhost\r\nUpgrade: websocket\r\nConnection: Upgrade\r\nSec-WebSocket-Key: dGhlIHNhbXBsZSBub25jZQ==\r\nSec-WebSocket-Version: 13\r\n\r\n"
           : "GET %s HTTP/1.1\r\nHost: localhost\r\nConnection: close\r\n\r\n",argv[2]);
    if(n<0 || n>=(int)sizeof(request) || exact(fd,request,(size_t)n,1)) return 7;
    if(!ws) {
        char data[4096];ssize_t r;size_t total=0;
        while((r=recv(fd,data,sizeof(data),0))>0) {
            if((total+=(size_t)r)>1024*1024) return 8;
            fwrite(data,1,(size_t)r,stdout);
        }
        close(fd);return total ? 0 : 9;
    }
    if(strcmp(argv[3],"--request-file")) return 10;
    size_t used=0;
    while(used<sizeof(request)-1) {
        if(exact(fd,request+used,1,0))return 11;
        request[++used]=0;
        if(used>=4 && !memcmp(request+used-4,"\r\n\r\n",4)) break;
    }
    if(!strstr(request," 101 ") || !strstr(request,"s3pPLMBiTxaQ9kYGzzhZRbK+xOo=")) {
        fprintf(stderr,"WebSocket upgrade rejected\n");return 12;
    }
    FILE *f=fopen(argv[4],"rb");if(!f)return 13;
    unsigned char *payload=malloc(65537);if(!payload)return 14;
    size_t size=fread(payload,1,65537,f);fclose(f);
    if(!size || size>65535)return 15;
    unsigned char header[8]={0x81,0};size_t hsize;
    if(size<126) {header[1]=0x80|(unsigned char)size;hsize=2;}
    else {header[1]=0xfe;header[2]=(unsigned char)(size>>8);header[3]=(unsigned char)size;hsize=4;}
    if(getrandom(header+hsize,4,0)!=4)return 16;
    for(size_t i=0;i<size;i++)payload[i]^=header[hsize+i%4];
    if(exact(fd,header,hsize+4,1)||exact(fd,payload,size,1))return 17;
    free(payload);
    for(unsigned count=0;count<24;count++) {
        unsigned char h[2],extra[8],mask[4];uint64_t len;
        if(exact(fd,h,2,0))return 18;
        len=h[1]&127;
        if(len==126) {if(exact(fd,extra,2,0))return 19;len=((uint64_t)extra[0]<<8)|extra[1];}
        else if(len==127) {if(exact(fd,extra,8,0))return 20;len=0;for(int i=0;i<8;i++)len=(len<<8)|extra[i];}
        if(len>4*1024*1024)return 21;
        if((h[1]&128)&&exact(fd,mask,4,0))return 22;
        char *body=malloc((size_t)len+1);if(!body)return 23;
        if(exact(fd,body,(size_t)len,0))return 24;
        if(h[1]&128)for(size_t i=0;i<len;i++)body[i]^=mask[i%4];
        body[len]=0;
        int found=(h[0]&15)==1 && (strstr(body,"\"id\":1,") || strstr(body,"\"id\":1}"));
        if(found) {puts(body);free(body);close(fd);return 0;}
        free(body);
        if((h[0]&15)==8)return 25;
    }
    close(fd);return 26;
}
