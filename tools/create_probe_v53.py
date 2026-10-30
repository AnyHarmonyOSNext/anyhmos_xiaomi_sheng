"""Correct donor namespace paths in the v52 SHA gate; no vendor changes."""
from pathlib import Path
import shutil,json
r=Path(__file__).resolve().parent.parent
for name in ['hmos_probe.c','probe_graphics.inc','probe_command.inc']:
    p=r/'tools/archive'/(Path(name).stem+'_v52'+Path(name).suffix)
    if not p.exists():shutil.copy2(r/'tools'/name,p)
shutil.copytree(r/'compat/sheng-graphics/v52',r/'compat/sheng-graphics/v53',dirs_exist_ok=True)
p=r/'compat/sheng-graphics/v53/apply-account-hmac.sh'
s=p.read_text().replace('/system/lib64/libhukssdk.z.so','/system/lib64/chipset-sdk/libhukssdk.z.so').replace('/system/lib64/libcrypto_openssl.z.so','/system/lib64/chipset-sdk-sp/libcrypto_openssl.z.so');p.write_bytes(s.encode())
p=r/'tools/hmos_probe.c';p.write_text(p.read_text().replace('v52','v53'))
shutil.copy2(r/'tools/configs/init-core-v52.cfg',r/'tools/configs/init-core-v53.cfg')
for stem in ['build_probe','verify']:
    (r/f'tools/{stem}_v53.py').write_text((r/f'tools/{stem}_v52.py').read_text().replace('v52','v53'))
p=r/'analysis/v52-framework.json';a=json.loads(p.read_text());a.update(status='FLASHED_STAGING_REJECTED_NAMESPACE_PATH_GUARD',evidence='output/logs/command-hmos-20261027-233552.log',result='Guard used wrong root alias for libhukssdk; aborted before native init; no account service test');p.write_text(json.dumps(a,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
a.update(version='v53',status='OFFLINE_CANDIDATE_NOT_FLASHED',result='Correct exact extracted donor namespace paths; same bridge and original account service env');(r/'analysis/v53-framework.json').write_text(json.dumps(a,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
