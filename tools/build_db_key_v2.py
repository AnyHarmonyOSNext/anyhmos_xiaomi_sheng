"""Build backwards-compatible database wrapping plus the narrow DE service route."""
from pathlib import Path
import hashlib
import json
import subprocess
r=Path('/mnt/c/SHENG_WORKSPACE')
sdk=Path('/root/hmos-work/sdk-6.0.0.47/installed/native')
d=r/'compat/sheng-framework/db-key-v2';link=r/'work/donor-hdi-link'
symbols=['SksGenerateRandom','SksGenerateKey','SksKeyExist','SksInit','SksUpdate','SksFinish','SksAbort','SksEncrypt','SksDecrypt',
         'DksGenerateRandom','DksGenerateKey','DksKeyExist','DksEncrypt','DksDecrypt']
(d/'exports.map').write_text('1.0 { global: '+'; '.join(symbols)+'; local: *; };\n')
flags=[str(sdk/'llvm/bin/clang'),'--target=aarch64-linux-ohos','-O2','-std=gnu11',
       '-Wall','-Wextra','-Werror','-Wno-misleading-indentation',
       '-I/root/hmos-work/graphics-deps/source/security_huks/interfaces/inner_api/huks_standard/main/include']
libs=[str(link/'libhukssdk.z.so'),str(link/'libcrypto_openssl.z.so'),'-Wl,--allow-shlib-undefined']
subprocess.run(flags+[str(d/'db_key.c'),'-shared','-fPIC','-Wl,-z,relro,-z,now',
    '-Wl,--version-script='+str(d/'exports.map'),'-Wl,-soname,libdbkeys.so',*libs,'-o',str(d/'libdbkeys.so')],check=True)
subprocess.run(flags+[str(d/'contract.c'),*libs,'-o',str(d/'db_key_contract')],check=True)
cpp=[str(sdk/'llvm/bin/clang++'),'--target=aarch64-linux-ohos','-O2','-std=c++17','-Wall','-Wextra','-Werror',
     '-nostdlib++','-include','/root/hmos-work/graphics-deps/sheng-graphics-port/tests/platform_cpp_config.h']
subprocess.run(cpp+[str(d/'manager_contract.cpp'),str(link/'libc++.so'),'-Wl,--allow-shlib-undefined',
    '-o',str(d/'manager_contract')],check=True)
result={}
for name in ['libdbkeys.so','db_key_contract','manager_contract']:
    p=d/name;subprocess.run([str(sdk/'llvm/bin/llvm-strip'),str(p)],check=True)
    result[name]=dict(bytes=p.stat().st_size,sha256=hashlib.sha256(p.read_bytes()).hexdigest())
result['scope']='Existing database keys/formats retained; new Dks imports route only distributed_db_root_key DE, other aliases/storage levels and import/delete remain HUKS.'
(d/'manifest.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps(result,indent=2))
