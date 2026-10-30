"""Persist collector output outside the guest root before investigating resets."""
from pathlib import Path
import shutil
r=Path(__file__).resolve().parent.parent
for n in ['hmos_probe.c','probe_graphics.inc','probe_command.inc']:
 p=r/'tools'/n;q=r/'tools/archive'/(p.stem+'_v59'+p.suffix)
 if not q.exists():shutil.copy2(p,q)
d=r/'compat/sheng-graphics/v60';assert not d.exists()
shutil.copytree(r/'compat/sheng-graphics/v59',d)
shutil.copy2(r/'tools/configs/init-core-v59.cfg',r/'tools/configs/init-core-v60.cfg')
p=r/'tools/hmos_probe.c';s=p.read_text().replace('v59','v60')
mark='static void watchdog(void) {'
assert s.count(mark)==1
fn='''static void runtime_persistent(void) {
    if(logfd>=0||traced_pid<=0)return;
    char marker[128];
    if(readfile("/sheng-persistent/hmos-compat/identity",marker,sizeof(marker))<=0||
       strcmp(marker,"sheng-hmos-data-v1\\n76fb5f0c-a521-4461-948d-60f2204655dc\\n"))return;
    char id[64];if(readfile("/proc/sys/kernel/random/boot_id",id,sizeof(id))<=0)return;
    id[strcspn(id,"\\r\\n")]=0;
    snprintf(logpath,sizeof(logpath),"/sheng-persistent/hmos-compat/probe-%s.log",id);
    logfd=open(logpath,O_CREAT|O_EXCL|O_WRONLY|O_CLOEXEC|O_NOFOLLOW,0600);
    if(logfd<0)return;
    allwrite(logfd,history,used);disk_bytes=used;
    note("PERSISTENT_RUNTIME_LOG=%s",logpath);fsync(logfd);
}
'''
s=s.replace(mark,fn+mark)
mark='flush_second=ts.tv_sec;if(traced_pid<=0)'
assert s.count(mark)==1
s=s.replace(mark,'flush_second=ts.tv_sec;runtime_persistent();if(traced_pid<=0)')
p.write_text(s)
for n in ['build_probe','verify']:
 (r/f'tools/{n}_v60.py').write_text((r/f'tools/{n}_v59.py').read_text().replace('v59','v60'))
print('v60 adds verified identity-gated durable collector logs')
