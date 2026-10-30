"""Build narrow database key wrapping and its on-device crypto contract."""
from pathlib import Path
import hashlib
import json
import subprocess
r=Path('/mnt/c/SHENG_WORKSPACE')
sdk=Path('/root/hmos-work/sdk-6.0.0.47/installed/native')
d=r/'compat/sheng-framework/db-key-v1'
link=r/'work/donor-hdi-link'
symbols=['SksGenerateRandom','SksGenerateKey','SksKeyExist','SksInit','SksUpdate','SksFinish','SksAbort','SksEncrypt','SksDecrypt']
(d/'exports.map').write_text('1.0 { global: '+ '; '.join(symbols)+'; local: *; };\n')
flags=[str(sdk/'llvm/bin/clang'),'--target=aarch64-linux-ohos','-O2','-std=gnu11',
       '-Wall','-Wextra','-Werror','-Wno-misleading-indentation',
       '-I/root/hmos-work/graphics-deps/source/security_huks/interfaces/inner_api/huks_standard/main/include']
libs=[str(link/'libhukssdk.z.so'),str(link/'libcrypto_openssl.z.so'),'-Wl,--allow-shlib-undefined']
subprocess.run(flags+[str(d/'db_key.c'),'-shared','-fPIC','-Wl,-z,relro,-z,now',
    '-Wl,--version-script='+str(d/'exports.map'),'-Wl,-soname,libdbkeys.so',*libs,'-o',str(d/'libdbkeys.so')],check=True)
subprocess.run(flags+[str(d/'contract.c'),*libs,'-o',str(d/'db_key_contract')],check=True)
result={}
for name in ['libdbkeys.so','db_key_contract']:
    p=d/name
    subprocess.run([str(sdk/'llvm/bin/llvm-strip'),str(p)],check=True)
    result[name]=dict(bytes=p.stat().st_size,sha256=hashlib.sha256(p.read_bytes()).hexdigest())
result['scope']='Only imported Sks* symbols in the original RDB/KV wrapping helpers; real per-UID software AES256-GCM, no TEE/authentication replacement'
(d/'manifest.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps(result,indent=2))
