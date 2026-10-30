"""Keep original code; route only the three identified database crypto imports."""
from pathlib import Path
import hashlib
import json
r=Path(__file__).resolve().parent.parent
d=r/'compat/sheng-framework/db-key-v2'
sha=lambda b:hashlib.sha256(b).hexdigest()
all_changes=[]
items=[('librelational_store_crypt.z.so','de22d9087b4b4eb2c4802f5987128cff11d9e3ff4692f619dd0e64df96577131','S'),
       ('libkv_store_crypt.z.so','1c2520958efe51b55a4fa3eb50ea740135dddc75499e0046d4861d97a6e86421','S'),
       ('libdistributeddatasvcfwk.z.so','77b6e7accf037cae71605f19848100e218c00c263f4fcff63445f74d1e4a86dd','D')]
for name,expected,prefix in items:
    raw=(r/'work/donor-hdi-link'/name).read_bytes();assert sha(raw)==expected
    b=bytearray(raw);changes=[]
    symbols=['HksGenerateRandom','HksGenerateKey','HksKeyExist','HksEncrypt','HksDecrypt']
    if prefix=='S':symbols+=['HksInit','HksUpdate','HksFinish','HksAbort']
    for old in [b'libhukssdk.z.so\0',*[s.encode()+b'\0' for s in symbols]]:
        count=raw.count(old)
        if count==0:
            assert prefix=='S' and old.startswith(b'Hks')
            continue
        assert count==1,(name,old,count)
        new=b'libdbkeys.so\0'.ljust(len(old),b'\0') if old.startswith(b'lib') else prefix.encode()+old[1:]
        off=raw.index(old);assert len(new)==len(old)
        b[off:off+len(old)]=new
        changes.append(dict(offset=off,before=old.hex(),after=new.hex()))
    if prefix=='D':
        assert len(changes)==6
        for s in ['HksAddParams','HksBuildParamSet','HksFreeParamSet','HksInitParamSet','HksImportKey','HksDeleteKey']:
            assert b.count(s.encode()+b'\0')==raw.count(s.encode()+b'\0')==1
    (d/name).write_bytes(b)
    all_changes.append(dict(name=name,input_sha256=sha(raw),output_sha256=sha(b),changes=changes))
lines=['#!/busybox sh','set -eu','B=/busybox','R=/hmos-root',
       '$B mkdir -p "$R/compat/lib64"',
       '$B cp /graphics/libdbkeys.so "$R/compat/lib64/libdbkeys.so"',
       f'echo "{sha((d/"libdbkeys.so").read_bytes())}  $R/compat/lib64/libdbkeys.so" | $B sha256sum -c -',
       '$B chmod 0644 "$R/compat/lib64/libdbkeys.so"',
       '$B mkdir -p "$R/data/service/el1/public/database/.sheng-dbkeys"',
       '$B chown 0:0 "$R/data/service/el1/public/database/.sheng-dbkeys"',
       '$B chmod 0711 "$R/data/service/el1/public/database/.sheng-dbkeys"',
       'while IFS=: read -r name pass uid gid rest; do',
       ' case "$uid" in ""|*[!0-9]*) continue;; esac',' [ "$uid" -lt 10000 ] || continue',
       ' P="$R/data/service/el1/public/database/.sheng-dbkeys/$uid"',
       ' $B mkdir -p "$P"; $B chown "$uid:$gid" "$P"; $B chmod 0700 "$P"',
       'done < "$R/system/etc/passwd"']
for item in all_changes:
    name=item['name'];lines += [f'S="$R/system/lib64/{name}"',f'T="$R/compat/lib64/{name}"',
        'sum=$($B sha256sum "$S"); sum=${sum%% *}',
        f'if [ "$sum" != {item["output_sha256"]} ]; then',
        f' [ "$sum" = {item["input_sha256"]} ] || exit 65','$B cp "$S" "$T"']
    for c in item['changes']:
        escaped=''.join('\\%03o'%x for x in bytes.fromhex(c['after']))
        lines += [f" $B printf '{escaped}' | $B dd of=\"$T\" bs=1 seek={c['offset']} conv=notrunc 2>/dev/null"]
    lines += [f' echo "{item["output_sha256"]}  $T" | $B sha256sum -c -',
              ' $B chmod 0644 "$T"; $B mount --bind "$T" "$S"','fi']
lines += ['echo DB_KEY_V2_SERVICE_DE_AND_CLIENT_WRAPPING_STAGED=1']
(d/'apply-db-key-v2.sh').write_text('\n'.join(lines)+'\n',encoding='utf-8',newline='\n')
(d/'patch.json').write_text(json.dumps(all_changes,indent=2)+'\n')
print(json.dumps([{k:v for k,v in c.items() if k!='changes'} for c in all_changes],indent=2))
