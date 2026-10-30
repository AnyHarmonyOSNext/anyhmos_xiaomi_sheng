"""Adapt the exact AnyHarmonyOS development patch to this donor with SHA guards."""
from pathlib import Path
import hashlib,json,re,subprocess

r=Path(__file__).resolve().parent.parent
reference='/root/hmos-reference/AnyHarmonyOS/sm8650/framework-patches/development-fsverity-compat.json'
upstream=json.loads(subprocess.check_output(['wsl','-d','Ubuntu-22.04','-u','root','--','cat',reference],text=True))
src=r/'work/hmos_system/system/system/lib64/libcode_sign_utils.z.so'
raw=src.read_bytes()
sha=lambda b:hashlib.sha256(b).hexdigest()
assert sha(raw)=='bbd86eec0b55323d61f6f27a7e3c132f7e7fbcdf3820f723d2db7dee40b0b4a9'
# This donor relocated the same four instructions. Require the whole sequence,
# uniqueness, original bytes and file SHA, rather than copying the old offset.
pattern=bytes.fromhex(upstream['guards'][0]['bytes']+upstream['changes'][0]['before']+upstream['guards'][1]['bytes'])
matches=[m.start() for m in re.finditer(re.escape(pattern),raw)]
assert matches==[0x12ce4],matches
site=matches[0]+len(bytes.fromhex(upstream['guards'][0]['bytes']))
out=bytearray(raw)
out[site:site+4]=bytes.fromhex(upstream['changes'][0]['after'])
d=r/'compat/sheng-framework/anyharmony-fsverity-dev-v1'
d.mkdir(exist_ok=True)
manifest={**upstream,'name':'sheng-anyharmony-fsverity-development-v1',
 'input_sha256':sha(raw),'output_sha256':sha(out),
 'changes':[{**upstream['changes'][0],'offset':site}],
 'guards':[{'offset':matches[0],'bytes':upstream['guards'][0]['bytes']},
           {'offset':site+4,'bytes':upstream['guards'][1]['bytes']}],
 'source_reference':{'repository':'YiKongk/AnyHarmonyOS','commit':'cb1ce16e71392404ecb56f812380ac18c7085520','path':'sm8650/framework-patches/development-fsverity-compat.json'},
 'disassembly':'VA0x13ce0 ioctl FS_IOC_GETFLAGS; 0x13ce4 preserves ioctl error; test FS_VERITY_FL; only absent-flag result -770 becomes0.',
 'scope':'Development bring-up only. Does not implement kernel code-integrity enforcement. Original donor and vendor remain untouched; private /compat/lib64 copy only.',
 'status':'offline guarded byte verification passed; runtime not yet tested'}
(d/'upstream-patch.json').write_text(json.dumps(upstream,indent=2)+'\n',encoding='utf-8')
(d/'patch.json').write_text(json.dumps(manifest,indent=2)+'\n',encoding='utf-8')
(d/'libcode_sign_utils.z.so').write_bytes(out)
(r/'analysis/anyharmony-fsverity-dev-v1.json').write_text(json.dumps(manifest,indent=2)+'\n',encoding='utf-8')
print(json.dumps(manifest,indent=2))
