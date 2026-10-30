"""Verify exported real Surface frame bytes against independent FFmpeg output."""
from pathlib import Path
import tarfile, hashlib, json
r=Path(__file__).resolve().parent.parent
artifact=r/'output/logs/v124-surface-verified.tar.gz'
report={}
with tarfile.open(artifact) as tar:
    for kind,ref in [('avc','reference.nv12'),('hevc','reference-hevc.nv12')]:
        data=tar.extractfile('v124-surface-'+kind+'.nv12').read()
        log=tar.extractfile('v124-surface-'+kind+'.txt').read().decode()
        assert data==(r/'work/video_decode_test'/ref).read_bytes()
        assert len(data)==73728 and log.count('SURFACE frame=')==12
        assert 'SURFACE_CONSUMED=12' in log and 'DECODE_RESULT=PASS' in log
        report[kind]=dict(frames=12,bytes=len(data),sha256=hashlib.sha256(data).hexdigest(),byte_for_byte_reference_match=True,real_consumer_surface=True)
report['artifact']=dict(path=str(artifact.relative_to(r)),sha256=hashlib.sha256(artifact.read_bytes()).hexdigest())
(r/'analysis/surface-v124-real-verification.json').write_text(json.dumps(report,indent=2)+'\n')
p=r/'analysis/metadata-v124-verification.json'; v=json.loads(p.read_text(encoding='utf-8-sig'))
v.update(status='flashed_readback_verified',cold_boot_verified=True,surface_decode_verified=True,boot_id='c2c5099b-9e8b-4c1a-95e9-e391437ed49d',autostart_seconds=180.93,autostart_exit=0,hardware_decode_verified=False,real_app_playback_verified=False)
p.write_text(json.dumps(v,indent=2)+'\n')
print(json.dumps(report,indent=2))
