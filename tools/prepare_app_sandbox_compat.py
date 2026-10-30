"""Expose only the hardware compatibility tree to the original app sandbox."""
from pathlib import Path
import gzip
import hashlib
import json

r=Path(__file__).resolve().parent.parent
report=[]
for name in ['appdata-sandbox.json', 'appdata-sandbox-isolated.json']:
    source=r/'work/hmos_system/system/system/etc/sandbox'/name
    raw=source.read_bytes(); cfg=json.loads(raw)
    count=0
    for common in cfg['common']:
        for base in common.get('app-base', []):
            mounts=base['mount-paths']
            assert not any(x['sandbox-path']=='/compat' for x in mounts)
            mounts.insert(0, {'src-path':'/compat','sandbox-path':'/compat',
                              'sandbox-flags':['bind','rec'], 'check-action-status':'true'})
            count+=1
    assert count==1
    out=(json.dumps(cfg,indent=2)+'\n').encode()
    dest=r/'work'/('compat-'+name)
    dest.write_bytes(out)
    dest.with_suffix(dest.suffix+'.gz').write_bytes(gzip.compress(out,mtime=0))
    report.append(dict(name=name,input_sha256=hashlib.sha256(raw).hexdigest(),
                       output_sha256=hashlib.sha256(out).hexdigest(),app_base_entries=count,
                       vendor_modified=False,authentication_modified=False))
(r/'analysis/app-sandbox-compat.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps(report,indent=2))
