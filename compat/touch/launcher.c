/* Supervise the unchanged tested THP bridge and publish its actual event node.
 * Started before MMI by the donor init; never read raw touch data here. */
#define _GNU_SOURCE
#include <dirent.h>
#include <errno.h>
#include <fcntl.h>
#include <signal.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/stat.h>
#include <sys/sysmacros.h>
#include <sys/wait.h>
#include <unistd.h>
static volatile sig_atomic_t bridge;
static void forward(int sig) { if (bridge > 0) kill(bridge, sig); }
static int publish(void)
{
    DIR *dir=opendir("/sys/class/input"); if(!dir)return 0;
    struct dirent *entry;int ready=0;
    while((entry=readdir(dir))) {
        if(strncmp(entry->d_name,"event",5)||!entry->d_name[5])continue;
        const char *p=entry->d_name+5;while(*p>='0'&&*p<='9')++p;if(*p)continue;
        char path[512],name[128];
        snprintf(path,sizeof(path),"/sys/class/input/%s/device/name",entry->d_name);
        FILE *file=fopen(path,"r");if(!file)continue;
        int match=fgets(name,sizeof(name),file)&&!strcmp(name,"Sheng THP Compat Touchscreen\n");fclose(file);if(!match)continue;
        snprintf(path,sizeof(path),"/sys/class/input/%s/dev",entry->d_name);
        unsigned major,minor;file=fopen(path,"r");if(!file)break;
        int fields=fscanf(file,"%u:%u",&major,&minor);fclose(file);if(fields!=2)break;
        snprintf(path,sizeof(path),"/dev/input/%s",entry->d_name);struct stat st;
        if(lstat(path,&st)) {
            if(errno!=ENOENT||mknod(path,S_IFCHR|0660,makedev(major,minor)))break;
        } else if(!S_ISCHR(st.st_mode)||st.st_rdev!=makedev(major,minor))break;
        if(chown(path,6696,6696)||chmod(path,0660))break;
        printf("THP_INPUT_NODE_READY path=%s major=%u minor=%u\n",path,major,minor);ready=1;break;
    }
    closedir(dir);return ready;
}
int main(void)
{
    int log=open("/data/local/tmp/sheng-thp-service.txt",O_WRONLY|O_CREAT|O_TRUNC|O_CLOEXEC,0600);
    if(log<0)return 2;dup2(log,1);dup2(log,2);close(log);setbuf(stdout,NULL);
    struct sigaction sa={0};sa.sa_handler=forward;sigemptyset(&sa.sa_mask);
    sigaction(SIGTERM,&sa,NULL);sigaction(SIGINT,&sa,NULL);
    pid_t child=fork();if(child<0)return 3;
    if(!child){execl("/compat/bin/sheng_thp_bridge","sheng_thp_bridge","--service",(char*)NULL);perror("exec bridge");_exit(127);}
    bridge=child;int status=0,ready=0;
    for(unsigned i=0;i<100;i++) {
        if(waitpid(child,&status,WNOHANG)==child){printf("THP_CHILD_EARLY_EXIT status=%d\n",status);return 4;}
        if(publish()){ready=1;break;}usleep(100000);
    }
    if(!ready){puts("THP_INPUT_NODE_MISSING");kill(child,SIGTERM);}
    while(waitpid(child,&status,0)<0)if(errno!=EINTR)return 5;
    bridge=0;printf("THP_CHILD_EXIT status=%d\n",status);
    return ready&&WIFEXITED(status)?WEXITSTATUS(status):6;
}
