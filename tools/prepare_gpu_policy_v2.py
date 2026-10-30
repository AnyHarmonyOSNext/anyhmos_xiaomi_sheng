from pathlib import Path
import shutil,json,hashlib
r=Path(__file__).resolve().parent.parent;d=r/'compat/sheng-graphics/gpu-policy-v2';d.mkdir(exist_ok=True)
shutil.copy2(r/'tools/sheng_gpu_policy.c',d/'sheng_gpu_policy.c')
shutil.copy2(r/'compat/sheng-graphics/static144-v1/sheng_gpu_policy',d/'sheng_gpu_policy')
# Freeze the earlier observer source alongside its earlier binaries.
new=(d/'sheng_gpu_policy.c').read_text(encoding='utf-8')
begin=new.index(' /* The first primary-node open')
end=new.index(' struct drm_set_client_cap',begin)
old=new[:begin]+new[end:]
for version in ['framepacing-v1','static144-v1']:
 p=r/'compat/sheng-graphics'/version
 (p/'sheng_gpu_policy.c').write_text(old,encoding='utf-8',newline='\n')
shutil.copy2(r/'compat/sheng-graphics/v89/sheng_gpu_policy',r/'compat/sheng-graphics/static144-v1/sheng_gpu_policy')
for dirname in ['framepacing-v1','static144-v1','gpu-policy-v2']:
 p=r/'compat/sheng-graphics'/dirname
 files=[f for f in p.iterdir() if f.is_file() and f.name!='manifest.json']
 (p/'manifest.json').write_text(json.dumps({f.name:{'bytes':f.stat().st_size,'sha256':hashlib.sha256(f.read_bytes()).hexdigest()} for f in files},indent=2)+'\n',encoding='utf-8')
# Preserve reproducibility of the previous v88/v89 sources.
for filename,dirname in [('build_framepacing_v1.py','framepacing-v1'),('build_static144_v1.py','static144-v1')]:
 p=r/'tools'/filename;s=p.read_text(encoding='utf-8').replace("str(r/'tools/sheng_gpu_policy.c')", "str(out/'sheng_gpu_policy.c')")
 p.write_text(s,encoding='utf-8',newline='\n')
print('frozen old source; new observer drops its own automatic DRM master')
