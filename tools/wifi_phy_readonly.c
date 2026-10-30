/* Read-only nl80211 GET_WIPHY dump using the running kernel's UAPI. */
/* This SDK's generated Linux socket header duplicates the libc tag. */
#define sockaddr_storage kernel_sockaddr_storage
#include <linux/netlink.h>
#include <linux/genetlink.h>
#include <linux/nl80211.h>
#undef sockaddr_storage
#include <sys/socket.h>
#include <sys/time.h>
#include <unistd.h>
#include <stdio.h>
#include <string.h>
#include <stdint.h>
#include <errno.h>

static int fd;
static unsigned sequence;
static unsigned char response[262144];
static int he_sta, eht_sta, records;
static int len(const struct nlattr *a) {return a->nla_len-NLA_HDRLEN;}
static void *data(const struct nlattr *a) {return (char *)a+NLA_HDRLEN;}
#define ATTRS(a, ptr, size) for (struct nlattr *a=(void *)(ptr); (size)>=NLA_HDRLEN && a->nla_len>=NLA_HDRLEN && a->nla_len<=(size); (size)-=NLA_ALIGN(a->nla_len), a=(void *)((char *)a+NLA_ALIGN(a->nla_len)))
static int send_request(int type, int cmd, int flags, int attr, const void *p, size_t n)
{
    unsigned char buf[256]={0};
    struct nlmsghdr *h=(void *)buf;
    struct genlmsghdr *g=(void *)(buf+NLMSG_HDRLEN);
    h->nlmsg_len=NLMSG_HDRLEN+GENL_HDRLEN;
    h->nlmsg_type=(unsigned short)type;
    h->nlmsg_flags=NLM_F_REQUEST|flags;
    h->nlmsg_seq=++sequence;
    g->cmd=(unsigned char)cmd;g->version=1;
    if(attr){
        struct nlattr *a=(void *)(buf+h->nlmsg_len);
        a->nla_type=(unsigned short)attr;a->nla_len=(unsigned short)(NLA_HDRLEN+n);
        if(n)memcpy(data(a),p,n);
        h->nlmsg_len+=NLA_ALIGN(a->nla_len);
    }
    struct sockaddr_nl peer={.nl_family=AF_NETLINK};
    return sendto(fd,buf,h->nlmsg_len,0,(void *)&peer,sizeof(peer))<0?-1:0;
}
static void read_iftype(struct nlattr *entry,int band)
{
    int remain=len(entry),station=0,he=0,eht=0;
    ATTRS(a,data(entry),remain){
        int t=a->nla_type&NLA_TYPE_MASK;
        if(t==NL80211_BAND_IFTYPE_ATTR_IFTYPES){
            int left=len(a);
            ATTRS(it,data(a),left)if((it->nla_type&NLA_TYPE_MASK)==NL80211_IFTYPE_STATION)station=1;
        }
        if(t==NL80211_BAND_IFTYPE_ATTR_HE_CAP_PHY)he=len(a);
        if(t==NL80211_BAND_IFTYPE_ATTR_EHT_CAP_PHY)eht=len(a);
    }
    if(station){
        printf("WIPHY_STATION band=%d he_phy_bytes=%d eht_phy_bytes=%d\n",band,he,eht);
        he_sta|=he>0;eht_sta|=eht>0;++records;
    }
}
static void read_bands(struct nlattr *bands)
{
    int left=len(bands);
    ATTRS(band,data(bands),left){
        int remain=len(band);
        ATTRS(field,data(band),remain){
            if((field->nla_type&NLA_TYPE_MASK)==NL80211_BAND_ATTR_IFTYPE_DATA){
                int size=len(field);
                ATTRS(entry,data(field),size)read_iftype(entry,band->nla_type&NLA_TYPE_MASK);
            }
        }
    }
}
int main(void)
{
    setvbuf(stdout,NULL,_IOLBF,0);alarm(15);
    fd=socket(AF_NETLINK,SOCK_RAW|SOCK_CLOEXEC,NETLINK_GENERIC);
    if(fd<0)return 2;
    struct sockaddr_nl local={.nl_family=AF_NETLINK};
    struct timeval tv={.tv_sec=3};
    if(bind(fd,(void *)&local,sizeof(local)))return 3;
    setsockopt(fd,SOL_SOCKET,SO_RCVTIMEO,&tv,sizeof(tv));
    if(send_request(GENL_ID_CTRL,CTRL_CMD_GETFAMILY,0,CTRL_ATTR_FAMILY_NAME,"nl80211",8))return 4;
    ssize_t n=recv(fd,response,sizeof(response),0);int family=0;
    if(n<=0)return 5;
    for(struct nlmsghdr *h=(void *)response;NLMSG_OK(h,n);h=NLMSG_NEXT(h,n)){
        if(h->nlmsg_type==NLMSG_ERROR)return 6;
        int remain=h->nlmsg_len-NLMSG_HDRLEN-GENL_HDRLEN;
        ATTRS(a,(char *)NLMSG_DATA(h)+GENL_HDRLEN,remain)
            if((a->nla_type&NLA_TYPE_MASK)==CTRL_ATTR_FAMILY_ID && len(a)==2)memcpy(&family,data(a),2);
    }
    if(!family)return 7;
    if(send_request(family,NL80211_CMD_GET_WIPHY,NLM_F_DUMP,NL80211_ATTR_SPLIT_WIPHY_DUMP,NULL,0))return 8;
    int done=0;
    while(!done){
        n=recv(fd,response,sizeof(response),0);
        if(n<=0){perror("netlink recv");return 9;}
        for(struct nlmsghdr *h=(void *)response;NLMSG_OK(h,n);h=NLMSG_NEXT(h,n)){
            if(h->nlmsg_seq!=sequence)continue;
            if(h->nlmsg_type==NLMSG_DONE){done=1;break;}
            if(h->nlmsg_type==NLMSG_ERROR){struct nlmsgerr *e=NLMSG_DATA(h);printf("NETLINK_ERROR=%d\n",e->error);return 10;}
            int remain=h->nlmsg_len-NLMSG_HDRLEN-GENL_HDRLEN;
            ATTRS(a,(char *)NLMSG_DATA(h)+GENL_HDRLEN,remain)
                if((a->nla_type&NLA_TYPE_MASK)==NL80211_ATTR_WIPHY_BANDS)read_bands(a);
        }
    }
    close(fd);
    printf("DRIVER_REPORTED_HE_STA=%d EHT_STA=%d records=%d\n",he_sta,eht_sta,records);
    return 0;
}
