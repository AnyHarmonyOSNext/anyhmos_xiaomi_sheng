"""Keep lifecycle/signal diagnostics without single-stepping forked JS apps."""
from pathlib import Path
import shutil
r=Path(__file__).resolve().parent.parent
for name in ['hmos_probe.c','probe_graphics.inc','probe_command.inc']:
    p=r/'tools'/name;dst=r/'tools/archive'/(p.stem+'_v56'+p.suffix)
    if not dst.exists():shutil.copy2(p,dst)
d=r/'compat/sheng-graphics/v57';assert not d.exists()
shutil.copytree(r/'compat/sheng-graphics/v56',d)
shutil.copy2(r/'tools/configs/init-core-v56.cfg',r/'tools/configs/init-core-v57.cfg')
p=r/'tools/hmos_probe.c';s=p.read_text().replace('v56','v57')
old='if(event==PTRACE_EVENT_FORK){unsigned long child=0;ptrace(PTRACE_GETEVENTMSG,traced_pid,0,&child);int added=0;'
assert s.count(old)==1
s=s.replace(old,old+'int child_syscalls=!(trace_hmos&&access("/hmos-native-hilog",F_OK)==0);')
old='trace_followers[i].syscalls=1;trace_followers[i].held=0;'
assert s.count(old)==1
s=s.replace(old,'trace_followers[i].syscalls=child_syscalls;trace_followers[i].held=0;')
old='ptrace(added?PTRACE_SYSCALL:PTRACE_DETACH,(pid_t)child,0,0)'
assert s.count(old)==1
s=s.replace(old,'ptrace(added?(child_syscalls?PTRACE_SYSCALL:PTRACE_CONT):PTRACE_DETACH,(pid_t)child,0,0)')
old='trace_followers[i].pid>0&&!trace_followers[i].held)return 1;'
assert s.count(old)==1
s=s.replace(old,'trace_followers[i].pid>0&&!trace_followers[i].held&&trace_followers[i].syscalls)return 1;')
s=s.replace('trace_followers_active())?100000:100000000','trace_followers_active())?100000:5000000')
p.write_text(s)
for name in ['build_probe','verify']:
    s=(r/f'tools/{name}_v56.py').read_text().replace('v56','v57')
    (r/f'tools/{name}_v57.py').write_text(s)
print('v57: native child forks use event/signal tracing immediately; original init early syscall observation retained')
