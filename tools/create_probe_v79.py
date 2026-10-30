"""Stage independent autonomous-start sources; preserve every v78 artifact."""
from pathlib import Path
import hashlib, shutil
r=Path(__file__).resolve().parents[1]
d=r/'compat/sheng-graphics/v79'
assert not d.exists()
shutil.copytree(r/'compat/sheng-graphics/v78', d)
for stem, suffix in [('hmos_probe','.c'),('probe_graphics','.inc'),('probe_command','.inc')]:
    src=r/f'tools/{stem}_v78{suffix}'
    (r/f'tools/{stem}_v79{suffix}').write_text(src.read_text(encoding='utf-8').replace('v78','v79'),encoding='utf-8',newline='\n')
shutil.copy2(r/'tools/configs/init-core-v78.cfg',r/'tools/configs/init-core-v79.cfg')
for stem in ['build_probe','verify']:
    s=(r/f'tools/{stem}_v78.py').read_text(encoding='utf-8').replace('v78','v79')
    if stem=='verify':
        s=s.replace("root/'compat/debug-tools/native_screenlock_request'", "root/'compat/debug-tools/native_screenlock_request_v2'")
        marker=" assert binary[:4]==b'\\x7fELF'"
        assert s.count(marker)==1
        s=s.replace(marker," assert b'AUTOSTART_SERVICES_READY=1' in new['graphics/start-native-desktop-v79.sh'][1]\n assert b'AUTOSTART bootstrap child=' in binary\n"+marker)
    (r/f'tools/{stem}_v79.py').write_text(s,encoding='utf-8',newline='\n')
old_sha=hashlib.sha256((d/'native_screenlock_request').read_bytes()).hexdigest()
shutil.copy2(r/'compat/debug-tools/native_screenlock_request_v2',d/'native_screenlock_request')
new_sha=hashlib.sha256((d/'native_screenlock_request').read_bytes()).hexdigest()
stage=(d/'apply-runtime-v78.sh').read_text(encoding='utf-8').replace('v78','v79').replace('V78','V79').replace(old_sha,new_sha)
(d/'apply-runtime-v79.sh').write_text(stage,encoding='utf-8',newline='\n')
(d/'apply-runtime-v78.sh').unlink()
shutil.copy2(r/'tools/start_native_desktop_v79.sh',d/'start-native-desktop-v79.sh')
shutil.copy2(r/'output/v49-native-graphics-installs-start.sh',d/'start-graphics-v79.sh')
# The helper must see a fresh capture result in each boot, not an old success.
p=d/'apply-runtime-v79.sh'
s=p.read_text(encoding='utf-8')
s=s.replace('$B mkdir -p $R/data/local/tmp/sheng-capture', '$B mkdir -p $R/data/local/tmp/sheng-capture\n$B rm -f $R/data/local/tmp/sheng-capture/display0.jpeg $R/data/local/tmp/v79-autostart-desktop.jpeg')
p.write_text(s,encoding='utf-8',newline='\n')
p=r/'tools/hmos_probe_v79.c'
s=p.read_text(encoding='utf-8')
s=s.replace(' * sheng HMOS bring-up probe. Static PID 1, no Android/OHOS service startup.\n * Only metadata/hmos-debug is written. Dynamic partitions are mapped read-only.',
''' * sheng HMOS autonomous compatibility bootstrap with diagnostic collector.
 * System changes are RAM overlays; framework data uses the existing ext4 file.
 * Vendor logical partitions remain read-only and are never covered.''')
s=s.replace('/* All upper layers and data are RAM-backed. Only read-only logical\n     * devices are exposed in this debug root; userdata is not exposed. */',
'''/* System upper layers are RAM-backed; /data is the existing ext4 file.
     * Only read-only logical devices are exposed in the native root. */''')
marker='                int out=open("/hmos-root/dev/kmsg",O_WRONLY|O_CLOEXEC);'
assert s.count(marker)==1
worker='''                if(kind==2){
                    pid_t boot=fork();
                    if(boot<0){note("AUTOSTART fork failed: %s; HOLD",strerror(errno));return;}
                    if(boot==0){
                        int input=open("/dev/null",O_RDONLY|O_CLOEXEC);
                        int output=open("/hmos-root/data/local/tmp/v79-autostart.txt",O_CREAT|O_TRUNC|O_WRONLY|O_CLOEXEC,0600);
                        if(input<0||output<0)_exit(126);
                        if(setsid()<0)_exit(126);
                        dup2(input,0);dup2(output,1);dup2(output,2);close(input);close(output);
                        if(serialfd>=0)close(serialfd);
                        if(logfd>=0)close(logfd);
                        if(watchfd>=0)close(watchfd);
                        execl("/busybox","busybox","timeout","300","/busybox","sh","/graphics/start-native-desktop-v79.sh",(char*)0);
                        _exit(127);
                    }
                    note("AUTOSTART bootstrap child=%ld; bounded=300s; original init follows",(long)boot);
                }
'''
s=s.replace(marker,worker+marker)
s=s.replace('sheng HMOS probe v79 -- diagnostic HOLD, no OS handoff, userdata access only on explicit hmos',
            'sheng HMOS probe v79 -- autonomous native startup; vendor read-only; existing isolated data only')
old='    note("PROBE COMPLETE; staying in PID 1. Reboot manually to Recovery and pull /metadata/hmos-debug. No Android/HMOS boot attempted.");'
assert s.count(old)==1
s=s.replace(old,'''    note("AUTOSTART loading verified IPC module before native init");
    ipc_load();trace_requested=3;''')
p.write_text(s,encoding='utf-8',newline='\n')
print('v79 independent assets staged; v78 preserved; not built/flashed')
