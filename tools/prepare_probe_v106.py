"""Persist verified time-clock port and restore missing native MemMgr SA1909."""
from pathlib import Path
import json
import shutil

r=Path(__file__).resolve().parent.parent
d=r/'compat/sheng-graphics/v106'
assert not d.exists()
shutil.copytree(r/'compat/sheng-graphics/v105',d)
for p in list(d.iterdir()):
    if p.is_file() and p.suffix in {'.cfg','.sh'}:
        q=p.with_name(p.name.replace('v105','v106'))
        data=p.read_text(encoding='utf-8').replace('v105','v106')
        if q!=p:p.unlink()
        q.write_text(data,encoding='utf-8',newline='\n')
for name in ['hmos_probe_v105.c','probe_graphics_v105.inc','probe_command_v105.inc',
             'build_probe_v105.py','verify_v105.py','start_native_desktop_v105.sh']:
    (r/'tools'/name.replace('v105','v106')).write_text(
        (r/'tools'/name).read_text(encoding='utf-8').replace('v105','v106'),newline='\n')
for name in ['init-core-v105.cfg','sheng-graphics-v105.hcs']:
    src=r/'tools/configs'/name
    if src.suffix=='.cfg':
        src.with_name(name.replace('v105','v106')).write_text(src.read_text().replace('v105','v106'),newline='\n')
    else:shutil.copy2(src,src.with_name(name.replace('v105','v106')))

shutil.copy2(r/'compat/sheng-framework/time-v1/apply-time-v1.sh',d/'apply-time-v1.sh')
p=d/'apply-runtime-v106.sh'
s=p.read_text()+'\n$B sh /graphics/apply-time-v1.sh\n'
p.write_text(s,newline='\n')

base=r/'work/hmos_system/system/system'
original=json.loads((base/'etc/init/memmgrservice.cfg').read_text())
service=original['services'][0]
assert service['name']=='memmgrservice'
# No fake Huawei hyperhold/cgroup files or hardware-specific VM tuning jobs.
# The stock Android kernel has no Huawei perf_critical cgroup.procs target.
service.pop('writepid')
service.update(disabled=1,once=1,sandbox=0,saspawn=False)
service['start-mode']='condition'
p=d/'init-platform-v106.cfg'
cfg=json.loads(p.read_text())
cfg['services'].append(service)
cfg['jobs'].append(dict(name='param:sheng-memmgr',condition='sheng.debug.start.memmgr=true',
                       cmds=original['jobs'][0]['cmds']))
p.write_text(json.dumps(cfg,indent=2)+'\n',newline='\n')
p=d/'start-native-desktop-v106.sh'
s=p.read_text()
marker='for gate in coredeps storaged; do $B chroot "$R" /system/bin/param set sheng.debug.start.$gate true; done\n$B sleep 2\n'
assert s.count(marker)==1
s=s.replace(marker,marker+'''stage=memmgr
$B chroot "$R" /system/bin/param set sheng.debug.start.memmgr true
deadline=$(($(now)+12))
while ! $B timeout 3 $B chroot "$R" /compat/bin/native_sa_check 1909; do
 if [ "$(now)" -ge "$deadline" ]; then echo MEMMGR_NOT_READY=1; break; fi
 $B sleep 1
done
stage=core
''')
p.write_text(s,newline='\n')
(r/'tools/start_native_desktop_v106.sh').write_text(s,newline='\n')
p=r/'tools/verify_v106.py'
s=p.read_text().replace("'av_codec_service','time_service'}","'av_codec_service','time_service','memmgrservice'}")
s=s.replace("'process.cfg','timeservice.cfg']:","'process.cfg','timeservice.cfg','memmgrservice.cfg']:")
s=s.replace("'socket','caps']:","'socket','caps','apl']:")
marker=" assert b'start-wifi-v106.sh' in binary"
assert s.count(marker)==1
s=s.replace(marker," assert b'sheng.debug.start.memmgr true' in new['graphics/start-native-desktop-v106.sh'][1]\n"
    +" assert new['graphics/apply-time-v1.sh'][1]==(root/'compat/sheng-framework/time-v1/apply-time-v1.sh').read_bytes()\n"
    +" assert b'apply-time-v1.sh' in new['graphics/apply-runtime-v106.sh'][1]\n"
    +" assert 'writepid' not in next(x for x in platform['services'] if x['name']=='memmgrservice')\n"
    +marker)
p.write_text(s,newline='\n')
print('v106 prepared: original MemMgr1909 and guarded 12-byte supported-timer port in RAM')
