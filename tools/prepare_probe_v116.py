"""Connect the tested original audio stack to native init; no vendor overlay."""
from pathlib import Path
import copy,json,shutil
r=Path(__file__).resolve().parent.parent
d=r/'compat/sheng-graphics/v116';assert not d.exists()
shutil.copytree(r/'compat/sheng-graphics/v115',d)
for p in list(d.iterdir()):
    if p.is_file() and p.suffix in {'.cfg','.sh'}:
        q=p.with_name(p.name.replace('v115','v116'))
        s=p.read_text(encoding='utf-8').replace('v115','v116')
        if p!=q:p.unlink()
        q.write_text(s,encoding='utf-8',newline='\n')
for name in ['hmos_probe_v115.c','probe_graphics_v115.inc','probe_command_v115.inc','build_probe_v115.py','verify_v115.py','start_native_desktop_v115.sh']:
    (r/'tools'/name.replace('v115','v116')).write_text((r/'tools'/name).read_text(encoding='utf-8').replace('v115','v116'),encoding='utf-8',newline='\n')
for name in ['init-core-v115.cfg','sheng-graphics-v115.hcs']:
    p=r/'tools/configs'/name;q=p.with_name(name.replace('v115','v116'))
    if p.suffix=='.cfg':q.write_text(p.read_text(encoding='utf-8').replace('v115','v116'),encoding='utf-8',newline='\n')
    else:shutil.copy2(p,q)
for src,name in [('apply_audio_v116.sh','apply-audio-v116.sh'),('start_audio_v116.sh','start-audio-v116.sh')]:
    shutil.copyfile(r/'tools'/src,d/name)
p=d/'init-hardware-v116.cfg';c=json.loads(p.read_text(encoding='utf-8'))
a=next(s for s in c['services'] if s['name']=='audio_server')
a['path']=['/compat/bin/native_audio_service_launcher']
host=copy.deepcopy(json.loads((r/'work/hmos_chip_prod/chip_prod/etc/init/hdf_devhost/audio_host.cfg').read_text())['services'][0])
host.pop('critical',None)
host.update(path=['/compat/bin/native_audio_service_launcher','host'],disabled=1,once=1,sandbox=0,saspawn=False)
host['start-mode']='condition'
c['services'].append(host)
job=next(j for j in c['jobs'] if j['name']=='param:sheng-audio')
job['cmds'].insert(-1,'start audio_host')
p.write_text(json.dumps(c,indent=2)+'\n',encoding='utf-8',newline='\n')
p=r/'tools/probe_graphics_v116.inc';s=p.read_text(encoding='utf-8')
marker='    note("HMOS two-host graphics trial staged in RAM;'
assert s.count(marker)==1
s=s.replace(marker,'    if(graphics_run_script("/graphics/apply-audio-v116.sh")<0)return -1;\n'+marker)
p.write_text(s,encoding='utf-8',newline='\n')
for p in [d/'start-native-desktop-v116.sh',r/'tools/start_native_desktop_v116.sh']:
    s=p.read_text(encoding='utf-8');marker='stage=netstack\n';assert s.count(marker)==1
    s=s.replace(marker,'stage=audio\nif [ -f /sheng-audio-v1/SHA256SUMS ]; then\n $B setsid $B timeout 120 $B sh /graphics/start-audio-v116.sh > "$R/data/local/tmp/v116-audio-startup.log" 2>&1 </dev/null &\n echo AUTOSTART_AUDIO_REQUESTED=1\nfi\n'+marker)
    p.write_text(s,encoding='utf-8',newline='\n')
p=r/'tools/verify_v116.py';s=p.read_text(encoding='utf-8')
s=s.replace("{'powermgr','media_service','av_session','audio_server'}","{'powermgr','media_service','av_session','audio_server','audio_host'}")
s+='\nassert b"apply-audio-v116.sh" in binary\nassert new["graphics/apply-audio-v116.sh"][1] == (root/"tools/apply_audio_v116.sh").read_bytes()\n'
s+='assert next(s for s in hardware["services"] if s["name"]=="audio_server")["path"]==["/compat/bin/native_audio_service_launcher"]\n'
p.write_text(s,encoding='utf-8',newline='\n')
print('v116 prepared: additive vendor_boot payload, real native init audio identities, no GPU change')
