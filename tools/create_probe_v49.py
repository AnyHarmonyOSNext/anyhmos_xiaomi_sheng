"""Isolate the new restorecon job and improve fatal/worker diagnostics."""
from pathlib import Path
import shutil,json
r=Path(__file__).resolve().parent.parent
for name in ['hmos_probe.c','probe_graphics.inc','probe_command.inc']:
    archive=r/'tools/archive'/(Path(name).stem+'_v48'+Path(name).suffix)
    if not archive.exists():shutil.copy2(r/'tools'/name,archive)
shutil.copytree(r/'compat/sheng-graphics/v48',r/'compat/sheng-graphics/v49',dirs_exist_ok=True)
c=(r/'tools/archive/hmos_probe_v48.c').read_text().replace('v48','v49')
old='note("PTRACED fatal pid=%ld signal=%d",(long)traced_pid,sig);if(!trace_allow_exit)'
new='''note("PTRACED fatal pid=%ld signal=%d",(long)traced_pid,sig);
#ifdef __aarch64__
        struct user_pt_regs fatal_regs;struct iovec fatal_io={.iov_base=&fatal_regs,.iov_len=sizeof(fatal_regs)};
        if(ptrace(PTRACE_GETREGSET,traced_pid,(void*)(uintptr_t)NT_PRSTATUS,&fatal_io)==0)
            note("FATAL_REGS pid=%ld pc=%llx sp=%llx lr=%llx fp=%llx",(long)traced_pid,(unsigned long long)fatal_regs.pc,(unsigned long long)fatal_regs.sp,(unsigned long long)fatal_regs.regs[30],(unsigned long long)fatal_regs.regs[29]);
        siginfo_t fatal_info;if(ptrace(PTRACE_GETSIGINFO,traced_pid,0,&fatal_info)==0)
            note("FATAL_SIGINFO code=%d address=%p",fatal_info.si_code,fatal_info.si_addr);
        char fatal_maps[64];snprintf(fatal_maps,sizeof(fatal_maps),"/proc/%ld/maps",(long)traced_pid);dump(fatal_maps);
#endif
        if(!trace_allow_exit)'''
assert c.count(old)==1
(r/'tools/hmos_probe.c').write_text(c.replace(old,new))
q=(r/'tools/archive/probe_command_v48.inc').read_text()
old='    command_output();if(command_pid<=0)return;\n'
new=old+'''    /* Native PID1 can be held on a fatal signal; reap only our worker here.
     * Do not depend on trace_poll(), which intentionally pauses in that state. */
    int worker_status;pid_t worker_done=waitpid(command_pid,&worker_status,WNOHANG);
    if(worker_done==command_pid){command_finish(worker_done,worker_status);return;}
'''
assert q.count(old)==1
(r/'tools/probe_command.inc').write_text(q.replace(old,new))
cfg=json.loads((r/'tools/configs/init-core-v48.cfg').read_text())
job=next(j for j in cfg['jobs'] if j['name']=='param:sheng-debug-coredeps')
job['cmds'].remove('restorecon -F /data/service/el1/public/access_token')
(r/'tools/configs/init-core-v49.cfg').write_text(json.dumps(cfg,indent=2)+'\n')
for a,b in [('build_probe_v48.py','build_probe_v49.py'),('verify_v48.py','verify_v49.py')]:
    (r/'tools'/b).write_text((r/'tools'/a).read_text().replace('v48','v49'))
(r/'analysis/v49-framework.json').write_text(json.dumps({
 'version':'v49','state':'OFFLINE_CANDIDATE_NOT_FLASHED',
 'v48_passed':['cold RAM ext4 data rw, 1.4GiB','private guarded framework DSO SHA','vendor/vendor_dlkm EROFS ro','native minimal core/HDF'],
 'v48_failed':'native init SIGSEGV immediately on coredeps gate, before new native service forks; added restorecon command is suspect, not yet proven',
 'changes':['remove only new restorecon call from coredeps job','capture PC/SP/LR/FP, siginfo and maps on fatal','reap exact USB worker even when native trace is held'],
 'limits':['no desktop','no completed BMS401 cold acceptance','GPU/service startup still manual gates','preserve real userdata and vendor']},indent=2)+'\n')
print('v49 source and assets staged')
