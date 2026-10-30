"""Copy licensed reference contracts, adjust their include path, build static AArch64."""
from pathlib import Path
import json,hashlib,subprocess
workspace=Path(__file__).resolve().parent.parent
reference=Path('/root/hmos-reference/AnyHarmonyOS/sm8650/kernel-port/tests')
output=Path('/root/hmos-work/sheng-ipc-tests');output.mkdir(exist_ok=True)
dest=workspace/'compat/sheng-hmos-ipc/tests';dest.mkdir(exist_ok=True)
manifest={}
for name in ['token_contract','binder_nested']:
    text=(reference/(name+'.c')).read_text().replace('#include "../module/access_tokenid.h"','#include "access_tokenid.h"')
    (output/(name+'.c')).write_text(text);(dest/(name+'.c')).write_text(text)
    subprocess.run(['aarch64-linux-gnu-gcc','-static','-O2','-Wall','-Wextra','-Wno-unused-parameter','-pthread','-I/root/hmos-work/sheng-hmos-ipc-exports',str(output/(name+'.c')),'-o',str(output/name)],check=True)
    subprocess.run(['aarch64-linux-gnu-strip',str(output/name)],check=True)
    data=(output/name).read_bytes();(dest/name).write_bytes(data)
    manifest[name]={'sha256':hashlib.sha256(data).hexdigest(),'bytes':len(data),'run_on_device':False}
(workspace/'analysis/ipc-contract-build.json').write_text(json.dumps(manifest,indent=2));print(json.dumps(manifest,indent=2))
