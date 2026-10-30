/* SPDX-License-Identifier: MIT
 * Local USB diagnostic command worker. PID1/collector stays responsive;
 * commands run in a separate process group with captured output and timeout.
 */
static pid_t command_pid;
static int command_fd=-1;
static char command_id[17];
static time_t command_deadline;
static int command_decode(const char *input,char *output,size_t capacity) {
    unsigned value=0,bits=0;size_t length=0;
    for(;*input&&*input!='=';input++){
        int digit=*input>='A'&&*input<='Z'?*input-'A':*input>='a'&&*input<='z'?*input-'a'+26:*input>='0'&&*input<='9'?*input-'0'+52:*input=='+'?62:*input=='/'?63:-1;
        if(digit<0)return -1;
        value=(value<<6)|(unsigned)digit;bits+=6;
        if(bits>=8){bits-=8;char c=(char)(value>>bits);if(!c||length+1>=capacity)return -1;output[length++]=c;}
    }output[length]=0;return length?0:-1;
}
static void command_output(void) {
    if(command_fd<0)return;
    char buffer[4096];for(int i=0;i<32;i++){ssize_t n=read(command_fd,buffer,sizeof(buffer));if(n>0)emit(buffer,(size_t)n);else break;}
}
static int command_finish(pid_t pid,int status) {
    if(pid!=command_pid||(!WIFEXITED(status)&&!WIFSIGNALED(status)))return 0;
    command_output();kill(-command_pid,SIGKILL);
    note("CMD END id=%s pid=%ld exit=%d signal=%d",command_id,(long)pid,WIFEXITED(status)?WEXITSTATUS(status):-1,WIFSIGNALED(status)?WTERMSIG(status):0);
    if(command_fd>=0)close(command_fd);
    command_fd=-1;command_pid=0;return 1;
}
static void command_tick(void) {
    command_output();if(command_pid<=0)return;
    /* Native PID1 can be held on a fatal signal; reap only our worker here.
     * Do not depend on trace_poll(), which intentionally pauses in that state. */
    int worker_status;pid_t worker_done=waitpid(command_pid,&worker_status,WNOHANG);
    if(worker_done==command_pid){command_finish(worker_done,worker_status);return;}
    struct timespec ts;clock_gettime(CLOCK_MONOTONIC,&ts);
    if(ts.tv_sec>=command_deadline){note("CMD timeout id=%s",command_id);kill(-command_pid,SIGKILL);command_deadline=ts.tv_sec+3600;}
}
static void command_start(const char *line) {
    if(command_pid>0){note("CMD rejected: command %s is running",command_id);return;}
    const char *space=strchr(line,' ');if(!space||space==line||(size_t)(space-line)>16){note("CMD invalid request identifier");return;}
    for(const char *p=line;p<space;p++)if(!((*p>='0'&&*p<='9')||(*p>='a'&&*p<='z')||(*p>='A'&&*p<='Z'))){note("CMD invalid identifier");return;}
    char script[3072];if(command_decode(space+1,script,sizeof(script))<0){note("CMD invalid or oversized base64 script");return;}
    size_t length=(size_t)(space-line);memcpy(command_id,line,length);command_id[length]=0;
    int pipefd[2];if(pipe2(pipefd,O_CLOEXEC|O_NONBLOCK)<0){note("CMD pipe failed: %s",strerror(errno));return;}
    pid_t child=fork();
    if(child==0){
        close(pipefd[0]);if(setsid()<0)_exit(126);umask(0022);
        int flags=fcntl(pipefd[1],F_GETFL);if(flags>=0)fcntl(pipefd[1],F_SETFL,flags&~O_NONBLOCK);
        dup2(pipefd[1],1);dup2(pipefd[1],2);close(pipefd[1]);
        int null=open("/dev/null",O_RDONLY|O_CLOEXEC);if(null>=0){dup2(null,0);close(null);}
        char *args[]={"/busybox","sh","-c",script,NULL};execv(args[0],args);dprintf(2,"debug command exec failed: %s\n",strerror(errno));_exit(126);
    }
    close(pipefd[1]);if(child<0){close(pipefd[0]);note("CMD fork failed: %s",strerror(errno));return;}
    struct timespec ts;clock_gettime(CLOCK_MONOTONIC,&ts);command_pid=child;command_fd=pipefd[0];command_deadline=ts.tv_sec+60;
    note("CMD BEGIN id=%s pid=%ld",command_id,(long)child);
}
