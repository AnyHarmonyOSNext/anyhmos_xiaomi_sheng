/* SPDX-License-Identifier: MIT
 * sheng HMOS bring-up probe. Static PID 1, no Android/OHOS service startup.
 * Only metadata/hmos-debug is written. Dynamic partitions are mapped read-only.
 */
#define _GNU_SOURCE
#include <stdio.h>
#include <stdint.h>
#include <stdlib.h>
#include <stdarg.h>
#include <string.h>
#include <errno.h>
#include <unistd.h>
#include <fcntl.h>
#include <dirent.h>
#include <signal.h>
#include <time.h>
#include <termios.h>
#include <sys/stat.h>
#include <sys/mount.h>
#include <sys/ioctl.h>
#include <sys/syscall.h>
#include <sys/sysmacros.h>
#include <sys/wait.h>
#include <linux/dm-ioctl.h>
#include <linux/watchdog.h>

#define CAP (2*1024*1024)
#define DISK_CAP (16*1024*1024)
static char history[CAP];
static size_t used, serial_pos, disk_bytes;
static int logfd=-1,kmsg=-1,serialfd=-1,watchfd=-1,consolefd=-1;
static char logpath[256], suffix[3]="_a";
static int slot_known;
static void allwrite(int fd,const void *buf,size_t n) {
    const char *p=buf;
    while(n) { ssize_t z=write(fd,p,n); if(z<0&&errno==EINTR)continue; if(z<=0)break; p+=z;n-=z; }
}
static void emit(const char *b,size_t n) {
    if(n>CAP)n=CAP;
    if(used+n>CAP) { size_t drop=used+n-CAP;memmove(history,history+drop,used-drop);used-=drop;serial_pos=serial_pos>drop?serial_pos-drop:0; }
    memcpy(history+used,b,n);used+=n;
    if(consolefd>=0)allwrite(consolefd,b,n);
    if(logfd>=0&&disk_bytes<DISK_CAP) {size_t z=n;if(z>DISK_CAP-disk_bytes)z=DISK_CAP-disk_bytes;allwrite(logfd,b,z);disk_bytes+=z;}
}
static void note(const char *fmt,...) {
    char b[2048];struct timespec ts;clock_gettime(CLOCK_MONOTONIC,&ts);
    int z=snprintf(b,sizeof(b),"[HMOS-PROBE %lld.%03ld] ",(long long)ts.tv_sec,ts.tv_nsec/1000000);
    va_list ap;va_start(ap,fmt);vsnprintf(b+z,sizeof(b)-(size_t)z,fmt,ap);va_end(ap);
    size_t n=strlen(b);if(n<sizeof(b)-1)b[n++]='\n';emit(b,n);
}
static ssize_t readfile(const char *p,char *b,size_t n) {
    int fd=open(p,O_RDONLY|O_CLOEXEC);if(fd<0)return -1;
    ssize_t z=read(fd,b,n-1);close(fd);if(z>=0)b[z]=0;return z;
}
static int put(const char *p,const char *v) {
    int fd=open(p,O_WRONLY|O_CLOEXEC);if(fd<0)return -1;
    ssize_t n=write(fd,v,strlen(v));int e=errno;close(fd);errno=e;return n==(ssize_t)strlen(v)?0:-1;
}
static void dump(const char *p) {char b[16384];ssize_t n=readfile(p,b,sizeof(b));note("FILE %s %s",p,n<0?strerror(errno):"");if(n>0)emit(b,(size_t)n);emit("\n",1);}
static void makedir(const char *p) {if(mkdir(p,0755)<0&&errno!=EEXIST)note("mkdir %s: %s",p,strerror(errno));}
static void drain(void) {
    char b[8192];if(kmsg<0)return;
    for(int i=0;i<1024;i++) {ssize_t n=read(kmsg,b,sizeof(b));if(n>0)emit(b,(size_t)n);else if(n<0&&errno==EPIPE)continue;else break;}
}
static int node_from_sys(const char *sys,const char *dst,mode_t type) {
    char p[512],b[128];unsigned a,c;snprintf(p,sizeof(p),"%s/dev",sys);
    if(readfile(p,b,sizeof(b))<0||sscanf(b,"%u:%u",&a,&c)!=2)return -1;
    if(mknod(dst,type|0600,makedev(a,c))<0&&errno!=EEXIST)return -1;
    return 0;
}
static void discover(void) {
    DIR *d=opendir("/sys/class/block");if(!d)return;struct dirent *de;
    while((de=readdir(d))) {if(de->d_name[0]=='.')continue;
        char sys[512],dst[512],path[1024],buf[8192];snprintf(sys,sizeof(sys),"/sys/class/block/%s",de->d_name);
        snprintf(dst,sizeof(dst),"/dev/block/%s",de->d_name);node_from_sys(sys,dst,S_IFBLK);
        snprintf(path,sizeof(path),"%s/uevent",sys);if(readfile(path,buf,sizeof(buf))<0)continue;
        char *p=strstr(buf,"PARTNAME=");if(!p)continue;p+=9;char *end=strchr(p,'\n');if(end)*end=0;
        if(!*p||strchr(p,'/')||strlen(p)>255)continue;
        snprintf(path,sizeof(path),"/dev/block/by-name/%s",p);
        if(access(path,F_OK)&&symlink(dst,path)<0&&errno!=EEXIST)note("by-name %s: %s",p,strerror(errno));
    }closedir(d);
}
static void persistent(void) {
    if(logfd>=0)return;
    char b[128];if(readfile("/dev/block/by-name/metadata",b,sizeof(b))<0)return;
    const char *fs[]={"f2fs","mifs","ext4"};int ok=0;
    for(unsigned i=0;i<sizeof(fs)/sizeof(fs[0]);i++) {
        if(mount("/dev/block/by-name/metadata","/metadata",fs[i],MS_NOSUID|MS_NODEV|MS_NOATIME,"")==0) {note("metadata mounted as %s (no format/fsck)",fs[i]);ok=1;break;}
        if(errno==EBUSY) {ok=1;break;}
    }
    if(!ok)return;
    if(mkdir("/metadata/hmos-debug",0700)<0&&errno!=EEXIST)return;
    char id[128]="unknown";readfile("/proc/sys/kernel/random/boot_id",id,sizeof(id));id[strcspn(id,"\r\n")]=0;
    snprintf(logpath,sizeof(logpath),"/metadata/hmos-debug/probe-%s.log",id);
    logfd=open(logpath,O_CREAT|O_EXCL|O_WRONLY|O_CLOEXEC|O_DSYNC|O_NOFOLLOW,0600);
    if(logfd<0)return;
    allwrite(logfd,history,used);disk_bytes=used;note("PERSISTENT_LOG=%s",logpath);fsync(logfd);
}
static void watchdog(void) {
    if(watchfd<0) {
        node_from_sys("/sys/class/watchdog/watchdog0","/dev/watchdog0",S_IFCHR);
        watchfd=open("/dev/watchdog0",O_WRONLY|O_CLOEXEC);
        if(watchfd>=0) {int t=120;ioctl(watchfd,WDIOC_SETTIMEOUT,&t);note("watchdog opened timeout=%d",t);}
    }
    if(watchfd>=0)ioctl(watchfd,WDIOC_KEEPALIVE,0);
}

struct mod {char name[128],deps[4096],pre[1024],post[1024];int state;};
static struct mod mods[1024];static int nmods;
static const char *basename_c(const char *p){const char *q=strrchr(p,'/');return q?q+1:p;}
static int same_module(const char *a,const char *b) {
    size_t an=strlen(a),bn=strlen(b);
    if(an>3&&!strcmp(a+an-3,".ko"))an-=3;
    if(bn>3&&!strcmp(b+bn-3,".ko"))bn-=3;
    if(an!=bn)return 0;
    for(size_t i=0;i<an;i++)if((a[i]=='_'?'-':a[i])!=(b[i]=='_'?'-':b[i]))return 0;
    return 1;
}
static void loadmod(const char *name,int depth);
static void load_words(const char *words,int depth) {
    char dep[4096];snprintf(dep,sizeof(dep),"%s",words);char *save,*p=strtok_r(dep," \r\n\t",&save);
    while(p){loadmod(p,depth+1);p=strtok_r(NULL," \r\n\t",&save);}
}
static void loadmod(const char *name,int depth) {
    if(depth>64)return;
    const char *base=basename_c(name);int idx=-1;
    for(int i=0;i<nmods;i++)if(same_module(mods[i].name,base)){idx=i;break;}
    if(idx>=0) {
        if(mods[idx].state)return;
        mods[idx].state=1;
        load_words(mods[idx].pre,depth);
        load_words(mods[idx].deps,depth);
        base=mods[idx].name;
    }
    char path[256];snprintf(path,sizeof(path),"/lib/modules/%.127s",base);int fd=open(path,O_RDONLY|O_CLOEXEC);
    if(fd<0){note("module missing %s",path);return;}
    int r=(int)syscall(SYS_finit_module,fd,"",0),e=errno;close(fd);
    if(r<0&&e!=EEXIST)note("module %s FAIL errno=%d %s",base,e,strerror(e));
    else note("module %s OK",base);
    if(idx>=0)mods[idx].state=r==0||e==EEXIST?2:0;
    drain();watchdog();
    if(idx>=0&&mods[idx].state==2)load_words(mods[idx].post,depth);
}
static void loadmodules(void) {
    FILE *f=fopen("/lib/modules/modules.dep","r");char line[8192];
    if(f) {while(fgets(line,sizeof(line),f)&&nmods<1024){char *p=strchr(line,':');if(!p)continue;*p++=0;snprintf(mods[nmods].name,sizeof(mods[nmods].name),"%.127s",basename_c(line));snprintf(mods[nmods].deps,sizeof(mods[nmods].deps),"%.4095s",p);nmods++;}fclose(f);}
    f=fopen("/lib/modules/modules.softdep","r");
    if(f){while(fgets(line,sizeof(line),f)){char module[128];if(sscanf(line,"softdep %127s",module)!=1)continue;int idx=-1;for(int j=0;j<nmods;j++)if(same_module(module,mods[j].name)){idx=j;break;}if(idx<0)continue;
        char *pre=strstr(line,"pre:"),*post=strstr(line,"post:");if(pre){pre+=4;if(post&&post>pre){size_t n=(size_t)(post-pre);if(n>=sizeof(mods[idx].pre))n=sizeof(mods[idx].pre)-1;memcpy(mods[idx].pre,pre,n);mods[idx].pre[n]=0;}else snprintf(mods[idx].pre,sizeof(mods[idx].pre),"%.1023s",pre);}if(post)snprintf(mods[idx].post,sizeof(mods[idx].post),"%.1023s",post+5);
    }fclose(f);}
    note("module hard/soft dependencies: %d",nmods);f=fopen("/lib/modules/modules.load","r");
    if(!f){note("FAIL no stock vendor ramdisk modules.load; use matching stock vendor_boot");return;}
    int i=0;while(fgets(line,sizeof(line),f)){line[strcspn(line,"# \t\r\n")]=0;if(*line)loadmod(line,0);if((++i%8)==0){discover();persistent();}}fclose(f);
    /* Normal first-stage modules.load omits the USB drivers that Android loads
     * later. These are present in this device's vendor recovery ramdisk. */
    const char *usbmods[]={"pinctrl-spmi-gpio.ko","pinctrl-spmi-mpp.ko","i2c-msm-geni.ko","pmic_glink.ko","ucsi_glink.ko","usb_bam.ko","phy-generic.ko","phy-msm-ssusb-qmp.ko","phy-msm-snps-eusb2.ko","phy-msm-m31-eusb2.ko","repeater.ko","repeater-qti-pmic-eusb2.ko","repeater-i2c-eusb2.ko","redriver.ko","eud.ko","ps5169.ko","dwc3-msm.ko"};
    for(unsigned j=0;j<sizeof(usbmods)/sizeof(usbmods[0]);j++){loadmod(usbmods[j],0);discover();persistent();}
}

/* SHA-256 for validating liblp geometry/header/table checksums before mapping. */
static uint32_t rr(uint32_t x,int n){return(x>>n)|(x<<(32-n));}
static void sha256(const void *data,size_t len,uint8_t out[32]) {
    static const uint32_t k[64]={0x428a2f98,0x71374491,0xb5c0fbcf,0xe9b5dba5,0x3956c25b,0x59f111f1,0x923f82a4,0xab1c5ed5,0xd807aa98,0x12835b01,0x243185be,0x550c7dc3,0x72be5d74,0x80deb1fe,0x9bdc06a7,0xc19bf174,0xe49b69c1,0xefbe4786,0x0fc19dc6,0x240ca1cc,0x2de92c6f,0x4a7484aa,0x5cb0a9dc,0x76f988da,0x983e5152,0xa831c66d,0xb00327c8,0xbf597fc7,0xc6e00bf3,0xd5a79147,0x06ca6351,0x14292967,0x27b70a85,0x2e1b2138,0x4d2c6dfc,0x53380d13,0x650a7354,0x766a0abb,0x81c2c92e,0x92722c85,0xa2bfe8a1,0xa81a664b,0xc24b8b70,0xc76c51a3,0xd192e819,0xd6990624,0xf40e3585,0x106aa070,0x19a4c116,0x1e376c08,0x2748774c,0x34b0bcb5,0x391c0cb3,0x4ed8aa4a,0x5b9cca4f,0x682e6ff3,0x748f82ee,0x78a5636f,0x84c87814,0x8cc70208,0x90befffa,0xa4506ceb,0xbef9a3f7,0xc67178f2};
    uint32_t h[8]={0x6a09e667,0xbb67ae85,0x3c6ef372,0xa54ff53a,0x510e527f,0x9b05688c,0x1f83d9ab,0x5be0cd19};
    const uint8_t *src=data;size_t total=((len+9+63)/64)*64;
    for(size_t off=0;off<total;off+=64){uint8_t b[64]={0};for(size_t j=0;j<64;j++){size_t x=off+j;if(x<len)b[j]=src[x];else if(x==len)b[j]=0x80;else if(x>=total-8)b[j]=(uint8_t)(((uint64_t)len*8)>>(8*(total-1-x)));}
        uint32_t w[64];for(int j=0;j<16;j++)w[j]=((uint32_t)b[j*4]<<24)|((uint32_t)b[j*4+1]<<16)|((uint32_t)b[j*4+2]<<8)|b[j*4+3];
        for(int j=16;j<64;j++)w[j]=w[j-16]+(rr(w[j-15],7)^rr(w[j-15],18)^(w[j-15]>>3))+w[j-7]+(rr(w[j-2],17)^rr(w[j-2],19)^(w[j-2]>>10));
        uint32_t a=h[0],bb=h[1],c=h[2],d=h[3],e=h[4],f=h[5],g=h[6],hh=h[7];
        for(int j=0;j<64;j++){uint32_t t1=hh+(rr(e,6)^rr(e,11)^rr(e,25))+((e&f)^((~e)&g))+k[j]+w[j];uint32_t t2=(rr(a,2)^rr(a,13)^rr(a,22))+((a&bb)^(a&c)^(bb&c));hh=g;g=f;f=e;e=d+t1;d=c;c=bb;bb=a;a=t1+t2;}
        h[0]+=a;h[1]+=bb;h[2]+=c;h[3]+=d;h[4]+=e;h[5]+=f;h[6]+=g;h[7]+=hh;
    }for(int i=0;i<32;i++)out[i]=(uint8_t)(h[i/4]>>(24-8*(i%4)));
}
static uint32_t u32(const void *p){uint32_t n;memcpy(&n,p,4);return n;}
static uint64_t u64(const void *p){uint64_t n;memcpy(&n,p,8);return n;}
static int digest_ok(uint8_t *b,size_t n,size_t at) {uint8_t expected[32],actual[32];memcpy(expected,b+at,32);memset(b+at,0,32);sha256(b,n,actual);memcpy(b+at,expected,32);return !memcmp(expected,actual,32);}
static void dm_init(void *buf,size_t sz,const char *name) {
    memset(buf,0,sz);struct dm_ioctl *d=buf;d->version[0]=4;d->version[1]=0;d->version[2]=0;d->data_size=(uint32_t)sz;d->data_start=sizeof(*d);snprintf(d->name,sizeof(d->name),"%s",name);
}
static int dm_map(const char *name,const uint8_t *ext,uint32_t n,uint32_t es,dev_t superdev) {
    int fd=open("/dev/mapper/control",O_RDWR|O_CLOEXEC);if(fd<0){note("DM control: %s",strerror(errno));return -1;}
    char buf[65536];struct dm_ioctl *d=(void*)buf;dm_init(buf,sizeof(buf),name);
    if(ioctl(fd,DM_DEV_CREATE,d)<0){note("DM create %s: %s",name,strerror(errno));close(fd);return -1;}
    dev_t dev=(dev_t)d->dev;dm_init(buf,sizeof(buf),name);d->flags=DM_READONLY_FLAG;d->target_count=n;
    size_t off=sizeof(*d);uint64_t logical=0;
    for(uint32_t i=0;i<n;i++){const uint8_t *e=ext+i*es;size_t start=off;struct dm_target_spec *t=(void*)(buf+off);off+=sizeof(*t);t->sector_start=logical;t->length=u64(e);logical+=t->length;strcpy(t->target_type,"linear");
        int z=snprintf(buf+off,sizeof(buf)-off,"%u:%u %llu",major(superdev),minor(superdev),(unsigned long long)u64(e+12));if(z<0||(size_t)z>=sizeof(buf)-off){close(fd);return -1;}off=(off+(size_t)z+1+7)&~7UL;t->next=(uint32_t)(off-start);}
    d->data_size=(uint32_t)off;
    if(ioctl(fd,DM_TABLE_LOAD,d)<0){note("DM load %s: %s",name,strerror(errno));close(fd);return -1;}
    dm_init(buf,sizeof(buf),name);if(ioctl(fd,DM_DEV_SUSPEND,d)<0){note("DM resume %s: %s",name,strerror(errno));close(fd);return -1;}
    char p[256];snprintf(p,sizeof(p),"/dev/mapper/%s",name);int r=mknod(p,S_IFBLK|0600,dev);close(fd);return r==0||errno==EEXIST?0:-1;
}
struct table {uint32_t off,num,es;};
static int table_get(const uint8_t *b,size_t ts,struct table *t,size_t at,size_t min) {
    t->off=u32(b+at);t->num=u32(b+at+4);t->es=u32(b+at+8);
    return t->es>=min&&t->num<=1024&&(uint64_t)t->off+(uint64_t)t->num*t->es<=ts;
}
static void partitions(const char *superpath,int inspect) {
    int fd=open(superpath,O_RDONLY|O_CLOEXEC);if(fd<0){note("super not found: %s",strerror(errno));return;}
    uint8_t geom[4096];int valid=0;
    for(int copy=0;copy<2;copy++){if(pread(fd,geom,sizeof(geom),4096+copy*4096)!=(ssize_t)sizeof(geom))continue;uint32_t size=u32(geom+4);if(u32(geom)==0x616c4467&&size>=52&&size<=4096&&digest_ok(geom,size,8)){valid=1;break;}}
    if(!valid){note("FAIL LP geometry/checksum");close(fd);return;}
    uint32_t max=u32(geom+40),slots=u32(geom+44);if(max<128||max>1048576||slots<1||slots>8){note("FAIL LP geometry bounds");close(fd);return;}
    if(!slot_known){note("FAIL active slot unknown; refusing to assume A or map partitions");close(fd);return;}
    unsigned slot=suffix[1]=='b'?1:0;if(slot>=slots){note("FAIL metadata slot out of range");close(fd);return;}
    uint8_t *b=malloc(max);if(!b){close(fd);return;}valid=0;uint32_t hs=0,ts=0;
    for(int backup=0;backup<2;backup++){off_t off=12288+(off_t)max*(slot+(backup?slots:0));if(pread(fd,b,max,off)!=(ssize_t)max)continue;hs=u32(b+8);ts=u32(b+44);
        if(u32(b)!=0x414c5030||b[4]!=10||hs<128||hs>max||ts>max-hs)continue;
        uint8_t sum[32];sha256(b+hs,ts,sum);
        if(digest_ok(b,hs,12)&&!memcmp(sum,b+48,32)){valid=1;note("LP slot=%u %s checksums OK",slot,backup?"backup":"primary");break;}}
    if(!valid){note("FAIL LP metadata/checksum");free(b);close(fd);return;}
    struct table pt,et,bt;if(!table_get(b,ts,&pt,80,52)||!table_get(b,ts,&et,92,24)||!table_get(b,ts,&bt,116,64)||bt.num!=1){note("FAIL LP tables/multiple block devices unsupported");free(b);close(fd);return;}
    uint8_t *tbl=b+hs;uint64_t super_size=u64(tbl+bt.off+16);struct stat st;fstat(fd,&st);
    unsigned found=0;
    for(uint32_t i=0;i<pt.num;i++){
        uint8_t *p=tbl+pt.off+i*pt.es;char name[37];memcpy(name,p,36);name[36]=0;uint32_t first=u32(p+40),n=u32(p+44);size_t ln=strlen(name);uint64_t size=0;
        if(!n||ln<2||strcmp(name+ln-2,suffix))continue;
        found++;
        if(n>64||first>et.num||n>et.num-first){note("FAIL extent bounds %s",name);continue;}int good=1;
        for(uint32_t j=0;j<n;j++){uint8_t *e=tbl+et.off+(first+j)*et.es;uint64_t sectors=u64(e),start=u64(e+12);if(u32(e+8)!=0||u32(e+20)!=0||start>super_size/512||sectors>super_size/512-start)good=0;size+=sectors*512;}
        note("PARTITION %s bytes=%llu extents=%u valid=%d",name,(unsigned long long)size,n,good);
        if(!good||inspect)continue;
        char dmname[128];snprintf(dmname,sizeof(dmname),"hmos_%s",name);if(dm_map(dmname,tbl+et.off+first*et.es,n,et.es,st.st_rdev)<0)continue;
        const char *mounts[]={"system","vendor","chip_prod","sys_prod","cust","vendor_dlkm"};
        for(unsigned j=0;j<sizeof(mounts)/sizeof(mounts[0]);j++){char expected[128];snprintf(expected,sizeof(expected),"%s%s",mounts[j],suffix);if(strcmp(name,expected))continue;
            char mp[256],dev[256];snprintf(mp,sizeof(mp),"/hmos/%s",mounts[j]);makedir(mp);snprintf(dev,sizeof(dev),"/dev/mapper/%s",dmname);
            int r=mount(dev,mp,"erofs",MS_RDONLY|MS_NOSUID|MS_NODEV,"");note("MOUNT %s -> %s ro result=%d errno=%d %s",dev,mp,r,r<0?errno:0,r<0?strerror(errno):"OK");
        }
    }if(!found)note("FAIL no populated logical partitions for active slot %s",suffix);
    free(b);close(fd);
}
static int usb_configured;
static void usb_setup(void) {
    if(usb_configured)return;
    DIR *d=opendir("/sys/class/udc");if(!d)d=opendir("/sys/class/UDC");if(!d)return;struct dirent *de;char controller[256]="";
    while((de=readdir(d)))if(de->d_name[0]!='.'){snprintf(controller,sizeof(controller),"%s",de->d_name);break;}
    closedir(d);if(!*controller)return;
    makedir("/config");if(mount("configfs","/config","configfs",MS_NOSUID|MS_NODEV|MS_NOEXEC,"")<0&&errno!=EBUSY){note("configfs: %s",strerror(errno));return;}
    const char *g="/config/usb_gadget/hmos_probe";makedir(g);char p[512];
#define ATTR(k,v) do{snprintf(p,sizeof(p),"%s/%s",g,k);if(put(p,v)<0)note("USB attr %s: %s",k,strerror(errno));}while(0)
    ATTR("idVendor","0x1d6b");ATTR("idProduct","0x0104");ATTR("bcdUSB","0x0200");ATTR("bcdDevice","0x0100");ATTR("bDeviceClass","0x02");
    makedir("/config/usb_gadget/hmos_probe/strings/0x409");ATTR("strings/0x409/serialnumber","sheng-hmos-probe");ATTR("strings/0x409/manufacturer","Local bring-up");ATTR("strings/0x409/product","sheng HMOS early log");
    makedir("/config/usb_gadget/hmos_probe/configs/c.1");ATTR("configs/c.1/MaxPower","250");
    makedir("/config/usb_gadget/hmos_probe/functions/acm.usb0");
    if(access("/config/usb_gadget/hmos_probe/functions/acm.usb0/port_num",F_OK)){note("FAIL USB ACM function unavailable");return;}
    if(symlink("/config/usb_gadget/hmos_probe/functions/acm.usb0","/config/usb_gadget/hmos_probe/configs/c.1/acm.usb0")<0&&errno!=EEXIST)note("USB function link: %s",strerror(errno));
    snprintf(p,sizeof(p),"%s/UDC",g);if(put(p,controller)<0){note("USB bind %s: %s",controller,strerror(errno));return;}usb_configured=1;note("USB ACM bound to %s",controller);
#undef ATTR
}
static void serial_tick(void) {
    if(serialfd<0&&usb_configured) {
        node_from_sys("/sys/class/tty/ttyGS0","/dev/ttyGS0",S_IFCHR);serialfd=open("/dev/ttyGS0",O_RDWR|O_NONBLOCK|O_NOCTTY|O_CLOEXEC);
        if(serialfd>=0){struct termios t;if(tcgetattr(serialfd,&t)==0){cfmakeraw(&t);t.c_cflag|=CLOCAL|CREAD;tcsetattr(serialfd,TCSANOW,&t);}serial_pos=0;note("USB ttyGS0 ready; commands: replay, status, sync");}
    }
    if(serialfd<0)return;
    char cmd[128];ssize_t n=read(serialfd,cmd,sizeof(cmd)-1);if(n>0){cmd[n]=0;if(strstr(cmd,"replay"))serial_pos=0;if(strstr(cmd,"status"))note("status: HOLD; %zu bytes history; persistent=%s",used,logfd>=0?logpath:"unavailable");if(strstr(cmd,"sync")&&logfd>=0)fsync(logfd);}
    if(serial_pos<used){size_t z=used-serial_pos;if(z>16384)z=16384;n=write(serialfd,history+serial_pos,z);if(n>0)serial_pos+=(size_t)n;}
}
static void slot_detect(void) {
    char b[32768];const char *files[]={"/proc/bootconfig","/proc/cmdline"};
    for(unsigned i=0;i<2;i++)if(readfile(files[i],b,sizeof(b))>0){char *p=strstr(b,"androidboot.slot_suffix");if(p){p=strchr(p,'=');if(p){p++;while(*p==' '||*p=='\t'||*p=='\"')p++;if(p[0]=='_'&&(p[1]=='a'||p[1]=='b')){suffix[1]=p[1];slot_known=1;}}}}
    note("active slot=%s known=%d",suffix,slot_known);
}
static void snapshots(void) {
    dump("/proc/cmdline");dump("/proc/bootconfig");dump("/proc/version");dump("/proc/partitions");dump("/proc/filesystems");dump("/proc/modules");dump("/proc/mounts");
    dump("/hmos/vendor/etc/fstab.KirinT93B");dump("/hmos/system/system/etc/ld-musl-aarch64.path");
    makedir("/sys/kernel/debug");mount("debugfs","/sys/kernel/debug","debugfs",MS_NOSUID|MS_NODEV|MS_NOEXEC,"");dump("/sys/kernel/debug/devices_deferred");
    dump("/sys/class/usb_role/a600000.ssusb-role-switch/role");dump("/sys/class/usb_role/a600000.dwc3-role-switch/role");
    const char *paths[]={"/hmos/system/system/bin/init","/hmos/system/system/lib/ld-musl-aarch64.so.1","/hmos/system/init"};
    for(unsigned i=0;i<3;i++){struct stat st;int r=lstat(paths[i],&st);note("ENTRY %s present=%d",paths[i],r==0);if(r==0&&S_ISLNK(st.st_mode)){char b[256];ssize_t n=readlink(paths[i],b,sizeof(b)-1);if(n>=0){b[n]=0;note("symlink -> %s",b);}}}
}
int main(int argc,char **argv) {
    if(argc==3&&!strcmp(argv[1],"--inspect-super")) {slot_known=1;if(getenv("HMOS_SLOT")&&!strcmp(getenv("HMOS_SLOT"),"b"))suffix[1]='b';partitions(argv[2],1);allwrite(1,history,used);return 0;}
    if(argc==2&&!strcmp(argv[1],"--sha-selftest")){uint8_t sum[32];sha256("abc",3,sum);for(int i=0;i<32;i++)printf("%02x",sum[i]);puts("");return 0;}
    if(getpid()!=1){fprintf(stderr,"This program must be init/PID 1. Use --inspect-super only for offline checks.\n");return 2;}
    umask(0077);signal(SIGPIPE,SIG_IGN);makedir("/dev");makedir("/proc");makedir("/sys");
    mount("tmpfs","/dev","tmpfs",MS_NOSUID,"mode=0755");mount("proc","/proc","proc",MS_NOSUID|MS_NODEV|MS_NOEXEC,"");mount("sysfs","/sys","sysfs",MS_NOSUID|MS_NODEV|MS_NOEXEC,"");
    mknod("/dev/kmsg",S_IFCHR|0600,makedev(1,11));mknod("/dev/null",S_IFCHR|0666,makedev(1,3));
    mknod("/dev/console",S_IFCHR|0600,makedev(5,1));consolefd=open("/dev/console",O_WRONLY|O_NONBLOCK|O_CLOEXEC);
    kmsg=open("/dev/kmsg",O_RDONLY|O_NONBLOCK|O_CLOEXEC);makedir("/dev/block");makedir("/dev/block/by-name");makedir("/dev/mapper");makedir("/metadata");makedir("/hmos");
#ifdef TRACE_ANDROID
    note("sheng HMOS trace v2 -- collect early logs, then execute original Android init");
#else
    note("sheng HMOS probe v2 -- diagnostic HOLD, no OS handoff, no userdata access");
#endif
    slot_detect();drain();discover();persistent();loadmodules();
    for(int i=0;i<50;i++){discover();persistent();drain();watchdog();usb_setup();serial_tick();usleep(100000);}
    char misc[2048];if(readfile("/proc/misc",misc,sizeof(misc))>0){char *save,*p=strtok_r(misc,"\n",&save);while(p){unsigned n;char name[128];if(sscanf(p,"%u %127s",&n,name)==2&&!strcmp(name,"device-mapper"))mknod("/dev/mapper/control",S_IFCHR|0600,makedev(10,n));p=strtok_r(NULL,"\n",&save);}}
    partitions("/dev/block/by-name/super",0);snapshots();drain();
#ifdef TRACE_ANDROID
    if(logfd<0&&serialfd<0) {
        note("TRACE ABORT: neither metadata log nor USB log endpoint available. HOLD instead of unobservable init handoff.");
    } else {
        note("TRACE HANDOFF: starting collector child and executing preserved 303 Android init; this is not an OHOS compatibility layer.");
        if(logfd>=0)fsync(logfd);
        pid_t child=fork();
        if(child>0){char *args[]={"/init",NULL};execv("/init.android.original",args);note("TRACE exec failed errno=%d %s; HOLD",errno,strerror(errno));}
        else if(child<0)note("TRACE fork failed: %s; HOLD",strerror(errno));
        else note("TRACE collector running pid=%ld",(long)getpid());
    }
#else
    note("PROBE COMPLETE; staying in PID 1. Reboot manually to Recovery and pull /metadata/hmos-debug. No Android/HMOS boot attempted.");
#endif
    unsigned tick=0;for(;;){drain();watchdog();serial_tick();while(waitpid(-1,NULL,WNOHANG)>0){}if((tick++%10)==0){discover();persistent();usb_setup();if(logfd>=0)fsync(logfd);}usleep(100000);}
}
