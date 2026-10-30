"""Fix the autonomous worker's stdio setup; keep failed v79 evidence."""
from pathlib import Path
import shutil
r=Path(__file__).resolve().parents[1]
d=r/'compat/sheng-graphics/v80'
assert not d.exists()
shutil.copytree(r/'compat/sheng-graphics/v79',d)
for p in list(d.iterdir()):
    if not p.is_file() or p.suffix!='.sh': continue
    name=p.name.replace('v79','v80')
    text=p.read_text(encoding='utf-8').replace('v79','v80').replace('V79','V80')
    if name!=p.name:p.unlink()
    (d/name).write_text(text,encoding='utf-8',newline='\n')
for stem,suffix in [('hmos_probe','.c'),('probe_graphics','.inc'),('probe_command','.inc')]:
    text=(r/f'tools/{stem}_v79{suffix}').read_text(encoding='utf-8').replace('v79','v80')
    (r/f'tools/{stem}_v80{suffix}').write_text(text,encoding='utf-8',newline='\n')
shutil.copy2(r/'tools/configs/init-core-v79.cfg',r/'tools/configs/init-core-v80.cfg')
for stem in ['build_probe','verify']:
    text=(r/f'tools/{stem}_v79.py').read_text(encoding='utf-8').replace('v79','v80')
    (r/f'tools/{stem}_v80.py').write_text(text,encoding='utf-8',newline='\n')
p=r/'tools/hmos_probe_v80.c'
s=p.read_text(encoding='utf-8')
old='''                        int input=open("/dev/null",O_RDONLY|O_CLOEXEC);
                        int output=open("/hmos-root/data/local/tmp/v80-autostart.txt",O_CREAT|O_TRUNC|O_WRONLY|O_CLOEXEC,0600);
                        if(input<0||output<0)_exit(126);
                        if(setsid()<0)_exit(126);
                        dup2(input,0);dup2(output,1);dup2(output,2);close(input);close(output);
                        if(serialfd>=0)close(serialfd);
                        if(logfd>=0)close(logfd);
                        if(watchfd>=0)close(watchfd);'''
assert s.count(old)==1
new='''                        if(setsid()<0)_exit(126);
                        /* PID1 may have opened its logger/watchdog on fd 0..2.
                         * Close inherited copies BEFORE opening new stdio.
                         * Do not close logger descriptor numbers after dup2. */
                        for(int fd=0;fd<1024;fd++)close(fd);
                        int input=open("/dev/null",O_RDONLY);
                        int output=open("/hmos-root/data/local/tmp/v80-autostart.txt",O_CREAT|O_TRUNC|O_WRONLY,0600);
                        if(input!=0||output!=1||dup2(output,2)!=2)_exit(126);
                        dprintf(1,"AUTOSTART_STDIO_READY input=0 output=1 error=2\\n");'''
s=s.replace(old,new)
p.write_text(s,encoding='utf-8',newline='\n')
shutil.copy2(d/'start-native-desktop-v80.sh',r/'tools/start_native_desktop_v80.sh')
print('v80 staged, inherited descriptors closed before stdio setup; not built/flashed')
