/* Bounded app-only tracer; pass every signal through and detach on timeout. */
#define _GNU_SOURCE
#include <asm/ptrace.h>
#include <dirent.h>
#include <elf.h>
#include <errno.h>
#include <fcntl.h>
#include <signal.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/ptrace.h>
#include <sys/uio.h>
#include <sys/wait.h>
#include <sys/syscall.h>
#include <time.h>
#include <unistd.h>
static pid_t tids[512]; static unsigned count;
static void remember(pid_t tid) { for(unsigned i=0;i<count;i++) if(tids[i]==tid)return; if(count<512)tids[count++]=tid; }
static void seize_threads(pid_t pid) {
    char path[64];snprintf(path,sizeof(path),"/proc/%d/task",pid);
    DIR *d=opendir(path);if(!d)return;struct dirent *e;
    while((e=readdir(d))) {
        pid_t t=atoi(e->d_name);if(t<=0)continue;
        unsigned i;for(i=0;i<count;i++)if(tids[i]==t)break;
        if(i<count)continue;
        if(ptrace(PTRACE_SEIZE,t,0,(void*)PTRACE_O_TRACECLONE)==0)remember(t);
    }
    closedir(d);
}
static pid_t find_app(void) {
    DIR *d=opendir("/proc"); if(!d)return 0; struct dirent *e; pid_t found=0;
    while((e=readdir(d))) {
        pid_t p=atoi(e->d_name); if(p<=1)continue;
        char path[64],name[256]={0}; snprintf(path,sizeof(path),"/proc/%d/cmdline",p);
        int f=open(path,O_RDONLY); if(f<0)continue; ssize_t n=read(f,name,sizeof(name)-1); close(f);
        if(n>0&&!strcmp(name,"com.ss.hm.ugc.aweme")){found=p;break;}
    } closedir(d); return found;
}
static void dump(pid_t pid,pid_t tid,int sig) {
    struct user_pt_regs r={0}; struct iovec v={&r,sizeof(r)};
    siginfo_t info={0}; ptrace(PTRACE_GETSIGINFO,tid,0,&info);
    int rc=ptrace(PTRACE_GETREGSET,tid,(void*)NT_PRSTATUS,&v);
    printf("APP_FATAL pid=%d tid=%d signal=%d addr=%p registers=%d pc=%llx lr=%llx sp=%llx fp=%llx\n",pid,tid,sig,info.si_addr,rc,r.pc,r.regs[30],r.sp,r.regs[29]);
    for(int i=0;i<31;i++)printf("X%d=%llx\n",i,r.regs[i]);
    char path[64]; snprintf(path,sizeof(path),"/proc/%d/maps",pid); FILE *f=fopen(path,"r");
    if(f){char line[1024];unsigned n=0;while(n++<2048&&fgets(line,sizeof(line),f))fputs(line,stdout);fclose(f);}
    unsigned long long stack[64]; struct iovec local={stack,sizeof(stack)}, remote={(void*)r.sp,sizeof(stack)};
    ssize_t n=process_vm_readv(pid,&local,1,&remote,1,0);
    for(ssize_t i=0;i<n/(ssize_t)sizeof(*stack);i++)printf("STACK+%03zx=%llx\n",i*sizeof(*stack),stack[i]);
}
static void detach_all(pid_t except) {
    for(unsigned i=0;i<count;i++)if(tids[i]!=except)ptrace(PTRACE_INTERRUPT,tids[i],0,0);
    for(unsigned i=0;i<count;i++)if(tids[i]!=except){
        int s; for(int n=0;n<100;n++){
            pid_t p=syscall(SYS_wait4,tids[i],&s,__WALL|WNOHANG,0);
            if(p==tids[i]){if(WIFSTOPPED(s))ptrace(PTRACE_DETACH,p,0,0);break;}
            if(p<0)break;
            usleep(1000);
        }
    }
}
int main(void) {
    setbuf(stdout,NULL); time_t until=time(NULL)+35; pid_t pid=0;
    while(time(NULL)<until&&!(pid=find_app()))usleep(50000);
    if(!pid){puts("NO_TARGET");return 2;}
    char statuspath[64];snprintf(statuspath,sizeof(statuspath),"/proc/%d/status",pid);
    FILE *statusfile=fopen(statuspath,"r");
    if(statusfile){char line[256];while(fgets(line,sizeof(line),statusfile))
        if(!strncmp(line,"Uid:",4)||!strncmp(line,"Gid:",4)||!strncmp(line,"Groups:",7))fputs(line,stdout);
        fclose(statusfile);}
    seize_threads(pid);printf("WATCH pid=%d threads=%u\n",pid,count);
    unsigned loops=0;
    while(time(NULL)<until) {
        if((++loops%10)==0)seize_threads(pid);
        int s;pid_t t=syscall(SYS_wait4,-1,&s,__WALL|WNOHANG,0);
        if(t<0&&errno!=EINTR&&errno!=ECHILD){printf("WAIT_ERROR=%d\n",errno);break;}
        if(t<=0){usleep(1000);continue;}
        printf("EVENT tid=%d status=%x\n",t,s);
        if(!WIFSTOPPED(s))continue;
        int sig=WSTOPSIG(s);unsigned event=(unsigned)s>>16;
        if(event==PTRACE_EVENT_CLONE){unsigned long child=0;ptrace(PTRACE_GETEVENTMSG,t,0,&child);remember(child);ptrace(PTRACE_CONT,t,0,0);continue;}
        if(event==PTRACE_EVENT_STOP){ptrace(PTRACE_CONT,t,0,0);continue;}
        if(sig==SIGSEGV||sig==SIGABRT||sig==SIGBUS||sig==SIGILL){dump(pid,t,sig);detach_all(t);ptrace(PTRACE_DETACH,t,0,(void*)(long)sig);puts("DETACHED_ALL");return 0;}
        ptrace(PTRACE_CONT,t,0,(void*)(long)sig);
    }
    detach_all(0);puts("TIMEOUT_DETACHED");return 0;
}
