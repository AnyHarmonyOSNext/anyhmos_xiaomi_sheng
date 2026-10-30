"""Add bounded crash evidence and a reversible no-password lock/unlock cycle."""
from pathlib import Path
r=Path(__file__).resolve().parents[1]
s=(r/'tools/native_screenlock_request_v3.cpp').read_text(encoding='utf-8')
s=s.replace('#include <pthread.h>','#include <pthread.h>\n#include <signal.h>\n#include <ucontext.h>\n#include <fcntl.h>\n#include <cstring>')
s=s.replace('int main()\n{', '''static void crash(int sig, siginfo_t* info, void* raw)
{
    auto* u = static_cast<ucontext_t*>(raw);
    dprintf(1,"SCREENLOCK_CRASH signal=%d address=%p pc=%llx lr=%llx sp=%llx\\n",sig,info->si_addr,
        (unsigned long long)u->uc_mcontext.pc,(unsigned long long)u->uc_mcontext.regs[30],
        (unsigned long long)u->uc_mcontext.sp);
    int fd=open("/proc/self/maps",O_RDONLY);char data[4096];ssize_t n;
    while(fd>=0&&(n=read(fd,data,sizeof(data)))>0)write(1,data,n);
    _exit(128+sig);
}
int main(int argc,char** argv)
{''')
s=s.replace('    setbuf(stdout, nullptr);', '''    setbuf(stdout, nullptr);
    struct sigaction action{};
    action.sa_sigaction=crash;action.sa_flags=SA_SIGINFO;
    sigaction(SIGSEGV,&action,nullptr);sigaction(SIGILL,&action,nullptr);sigaction(SIGABRT,&action,nullptr);''')
s=s.replace('    bool locked = manager->IsScreenLocked();', '''    if (argc==2 && !std::strcmp(argv[1],"--cycle")) {
        int ret=manager->Lock(100);
        std::printf("SCREENLOCK_CYCLE_LOCK ret=%d\\n",ret);
        if(ret!=E_SCREENLOCK_OK)return 9;
        sleep(2);
    }
    bool locked = manager->IsScreenLocked();''')
(r/'tools/native_screenlock_request_v4.cpp').write_text(s,encoding='utf-8',newline='\n')
s=(r/'tools/build_screenlock_request_v3.py').read_text(encoding='utf-8').replace('v3','v4')
(r/'tools/build_screenlock_request_v4.py').write_text(s,encoding='utf-8',newline='\n')
print('v4 diagnostic source staged')
