from pathlib import Path
import subprocess,os,json,hashlib
root=Path.cwd();cmd=['wsl','-d','Ubuntu-22.04','--','bash','-lc']
# Native parser runs read-only. Mutations here affect tiny local metadata fixtures only.
p=root/'analysis/hmos_super_metadata.raw';b=p.read_bytes()
fixtures={
 'bad-geometry': [(4096+8,1),(8192+8,1)],
 'primary-corrupt':[(12288+12,1)],
 'both-corrupt':[(12288+12,1),(12288+65536*3+12,1)]}
results={}
for name,changes in fixtures.items():
 c=bytearray(b)
 for off,val in changes:c[off]^=val
 (root/f'analysis/test-{name}.raw').write_bytes(c)
 shell=f'cd "/mnt/c/SHENG_WORKSPACE" && work/hmos_probe_host --inspect-super analysis/test-{name}.raw'
 r=subprocess.run(cmd+[shell],capture_output=True,text=True,encoding='utf-8');assert r.returncode==0;rout=r.stdout;print(name,rout.strip());results[name]=rout
assert 'FAIL LP geometry/checksum' in results['bad-geometry']
assert 'backup checksums OK' in results['primary-corrupt'] and 'PARTITION system_a' in results['primary-corrupt']
assert 'FAIL LP metadata/checksum' in results['both-corrupt'] and 'PARTITION ' not in results['both-corrupt']
(root/'analysis/parser-negative-tests.json').write_text(json.dumps(results,indent=2))
files={}
for p in (root/'output').rglob('*'):
 if p.is_file() and p.name not in ['package-manifest.json','manifest.json']:
  with p.open('rb') as f:h=hashlib.file_digest(f,'sha256').hexdigest()
  files[p.relative_to(root/'output').as_posix()]={'Bytes':p.stat().st_size,'Sha256':h}
(root/'output/package-manifest.json').write_text(json.dumps(files,indent=2),encoding='utf-8')
print('Package manifest:',len(files),'files')
