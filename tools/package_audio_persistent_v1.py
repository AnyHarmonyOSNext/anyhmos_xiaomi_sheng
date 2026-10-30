"""Stage verified audio assets for an additive original vendor ramdisk payload."""
from pathlib import Path
import gzip, hashlib, json, shutil, tarfile

r=Path(__file__).resolve().parent.parent
d=r/'work/audio-persistent-v1'
d.mkdir(exist_ok=True)
def add(src,name):
    p=d/name; p.parent.mkdir(parents=True,exist_ok=True)
    shutil.copyfile(src,p)
def put(name,data):
    p=d/name; p.parent.mkdir(parents=True,exist_ok=True); p.write_bytes(data)
for runtime,target in [('audio-bionic-v1','audio-runtime'),('audio-pal-v1','audio-pal-v1'),('audio-supplement-v1','audio-supplement-v1')]:
    for p in (r/'work'/runtime).rglob('*'):
        if p.is_file() and p.relative_to(r/'work'/runtime).parts[0] in ['bin','lib64','config','firmware']:
            add(p,str(Path(target)/p.relative_to(r/'work'/runtime)))
add(r/'work/audio-bionic-v1/lib64/libc++.so','audio-runtime/lib64/libc++_vndk33.so')
put('audio-runtime/lib64/libc++.so',gzip.decompress((r/'output/system-libcxx-303.so.gz').read_bytes()))
for p in (r/'work/stock-audio-runtime/odm/etc/acdbdata/Forte').iterdir():
    if p.is_file(): add(p,'audio-runtime/acdb/Forte/'+p.name)
for src,name in [
 ('compat/sheng-audio/pal-lifecycle-v1/libsheng_pal_lifecycle.so','audio-pal-v1/libsheng_pal_lifecycle_clean.so'),
 ('work/audio-pal-v1/libsheng_audio_paths.so','audio-pal-v1/libsheng_audio_paths.so'),
 ('compat/sheng-audio/pal-bridge-v1/libsheng_pal_server.so','audio-pal-v1/libsheng_pal_server_v1c.so'),
 ('compat/sheng-audio/pd-mapper-v1/sheng-pd-mapper','audio/bin/sheng-pd-mapper'),
]: add(r/src,name)
for name in ['libsheng_audio_vdi.so','libsheng_audio_vdi_loader.so','libsheng_audio_manager_service.so']:
    add(r/'compat/sheng-audio/pal-bridge-v1'/name,'audio/native/lib64/'+name)
for name in ['native_audio_hdi_publisher','native_audio_service_launcher','native_system_audio_check']:
    add(r/'compat/debug-tools'/name,'audio/native/bin/'+name)
for name in ['qrtr-smd','qcom_q6v5_pas','smp2p','audio-transport','audio-card','audio_pkt_dlkm','wcd938x_slave_dlkm','bt_fm_slim','slim-qcom-ngd-ctrl']:
    add(r/'output'/f'load-official303-{name}.sh',f'audio/scripts/load-official303-{name}.sh')
for src,name in [('stage_audio_firmware.sh','stage-audio-firmware.sh'),('stage_audio_nodes.sh','stage-audio-nodes.sh'),('stage_audio_supplement.sh','stage-audio-supplement.sh')]:
    add(r/'tools'/src,'audio/scripts/'+name)
with tarfile.open(r/'output/audio-policy-donor-min-v1.tar.gz') as t:
    for member in t:
        if not member.isfile(): continue
        p=Path(member.name); assert not p.is_absolute() and '..' not in p.parts
        f=t.extractfile(member); assert f
        put(str(Path('audio/policy')/p),f.read())
files={str(p.relative_to(d)).replace('\\','/'):dict(bytes=p.stat().st_size,sha256=hashlib.sha256(p.read_bytes()).hexdigest()) for p in sorted(d.rglob('*')) if p.is_file() and p.name not in ['SHA256SUMS','manifest.json']}
(d/'SHA256SUMS').write_text(''.join(f"{v['sha256']}  {k}\n" for k,v in files.items()),encoding='ascii',newline='\n')
(d/'manifest.json').write_text(json.dumps(dict(scope='Additive /sheng-audio-v1 payload; original vendor entries preserved',files=files),indent=2)+'\n')
print(json.dumps(dict(files=len(files),bytes=sum(v['bytes'] for v in files.values()),manifest_sha256=hashlib.sha256((d/'SHA256SUMS').read_bytes()).hexdigest())))
