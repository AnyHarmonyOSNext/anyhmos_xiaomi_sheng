"""v52: account-only software HMAC, leaving the original TEE service gated."""
from pathlib import Path
import shutil,json,hashlib
r=Path(__file__).resolve().parent.parent
for name in ['hmos_probe.c','probe_graphics.inc','probe_command.inc']:
    archive=r/'tools/archive'/(Path(name).stem+'_v51'+Path(name).suffix)
    if not archive.exists():shutil.copy2(r/'tools'/name,archive)
d=r/'compat/sheng-graphics/v52';shutil.copytree(r/'compat/sheng-graphics/v51',d,dirs_exist_ok=True)
for name in ['libsheng_account_hmac.so','account_hmac_contract']:
    shutil.copy2(r/'compat/sheng-framework/account-hmac-v1'/name,d/name)
guard=json.loads((r/'compat/sheng-framework/account-hmac-v1/manifest.json').read_text())
script='''#!/bin/sh
set -eu
B=/busybox
R=/hmos-root
'''
for name,sha in guard['donor'].items():
    script+=f'h=$($B sha256sum "$R/system/lib64/{name}"); case "$h" in {sha}*) ;; *) echo ACCOUNT_HMAC_DONOR_MISMATCH_{name}; exit 51;; esac\n'
script+='''$B cp /graphics/libsheng_account_hmac.so "$R/compat/lib64/libsheng_account_hmac.so"
$B chmod 0644 "$R/compat/lib64/libsheng_account_hmac.so"
$B cp /graphics/account_hmac_contract "$R/data/local/tmp/account_hmac_contract"
$B chmod 0755 "$R/data/local/tmp/account_hmac_contract"
'''
sha=guard['libsheng_account_hmac.so']['sha256']
script+=f'h=$($B sha256sum "$R/compat/lib64/libsheng_account_hmac.so"); case "$h" in {sha}*) ;; *) echo ACCOUNT_HMAC_OUTPUT_MISMATCH; exit 52;; esac\n'
script+='echo SHENG_ACCOUNT_HMAC_STAGED_NO_TEE_OR_AUTH_CLAIM\n'
(d/'apply-account-hmac.sh').write_bytes(script.encode())
c=(r/'tools/archive/hmos_probe_v51.c').read_text().replace('v51','v52')
(r/'tools/hmos_probe.c').write_text(c)
g=(r/'tools/archive/probe_graphics_v51.inc').read_text()
line='    if(graphics_run_script("/graphics/apply-framework-dev.sh")<0)return -1;'
assert g.count(line)==1
g=g.replace(line,line+'\n    if(graphics_run_script("/graphics/apply-account-hmac.sh")<0)return -1;')
(r/'tools/probe_graphics.inc').write_text(g)
cfg=json.loads((r/'tools/configs/init-core-v51.cfg').read_text())
account=next(s for s in cfg['services'] if s['name']=='accountmgr')
account['env']=[{'name':'LD_PRELOAD','value':'/compat/lib64/libsheng_account_hmac.so'}]
raw=(json.dumps(cfg,indent=2)+'\n').encode();assert len(raw)<32768
(r/'tools/configs/init-core-v52.cfg').write_bytes(raw)
for a,b in [('build_probe_v51.py','build_probe_v52.py'),('verify_v51.py','verify_v52.py')]:
    text=(r/'tools'/a).read_text().replace('v51','v52');(r/'tools'/b).write_text(text)
(r/'analysis/v52-framework.json').write_text(json.dumps({'version':'v52','status':'OFFLINE_CANDIDATE_NOT_FLASHED','scope':'account-only HMAC-SHA256 in /compat; TEE investigation postponed; original account identity/permissions preserved','config_bytes':len(raw),'contract_evidence':'output/logs/command-shell-20261027-232934-eea6491c0c5a.log','contract':'RFC4231 + original donor param-set ABI + real random key storage + streaming HMAC + consumed-handle rejection passed on v51','donor_and_upstream':guard,'desktop':False,'vendor_modified':False,'real_userdata_mounted':False},ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print('v52 config',len(raw))
