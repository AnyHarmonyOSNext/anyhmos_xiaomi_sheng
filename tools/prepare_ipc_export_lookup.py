"""Use supported canonical GPL symbol lookup instead of raw kprobe addresses.

Requires the separately built shim-export GKI. Missing export fails closed.
"""
from pathlib import Path
import difflib,shutil,re
root=Path(__file__).resolve().parent.parent
target=Path('/root/hmos-work/sheng-hmos-ipc-exports')
base=Path('/root/hmos-work/sheng-hmos-ipc')
target.mkdir(exist_ok=True)
for p in base.iterdir():
    if p.suffix in ['.c','.h'] and not p.name.endswith('.mod.c') or p.name=='Makefile':
        if not (target/p.name).exists():shutil.copyfile(p,target/p.name)
p=target/'private_api.c';before=(base/p.name).read_text()
header=root/'compat/sheng-hmos-ipc/api/sheng_hmos_api_v1.h'
shutil.copyfile(header,target/header.name)
start=before.index('static int resolve_api(');end=before.index('\nint ace5_private_api_init',start)
init_end=before.index('\n/* Header inline helpers',end)
names=re.findall(r'resolve_api\("([^"]+)"',before)
resolve='''int ace5_private_api_init(void)
{
    const struct sheng_hmos_ipc_api_v1 *api = __symbol_get("sheng_hmos_ipc_api_v1");
    if (!api) {
        pr_err("SHENG_IPC missing typed kernel API table; compatible kernel required\\n");
        return -ENOENT;
    }
    if (api->magic != SHENG_HMOS_API_MAGIC || api->version != 1 || api->size != sizeof(*api)) {
        pr_err("SHENG_IPC kernel API table version/layout mismatch\\n");
        __symbol_put("sheng_hmos_ipc_api_v1");
        return -ELIBBAD;
    }
'''+''.join(f'''    if (!api->api_{name}) return -ELIBBAD;
    ace5_api_{name} = api->api_{name};
    pr_info("SHENG_IPC typed-canonical name={name} address=%px\\n", api->api_{name});
''' for name in names)+'''
    return 0;
}
'''
after=before[:start]+resolve+before[init_end:]
after=after.replace('#include <linux/kprobes.h>','#include <linux/module.h>\n#include "sheng_hmos_api_v1.h"')
assert p.read_text() in (before,after) or 'missing canonical GPL export' in p.read_text()
p.write_text(after)
(root/'analysis/sheng-ipc-export-lookup.patch').write_text(''.join(difflib.unified_diff(before.splitlines(True),after.splitlines(True),fromfile='v15/private_api.c',tofile='v16/private_api.c')))
print('Typed read-only kernel API table lookup prepared; stock kernel fails closed.')
