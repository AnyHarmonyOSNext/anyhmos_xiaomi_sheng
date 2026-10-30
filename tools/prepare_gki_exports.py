"""Run in WSL: add typed GPL exports in an isolated exact-stock GKI worktree.

This preserves stock CFI enforcement, structure layout and old export ABI.
It never flashes images or changes the stock source/build directories.
"""
from pathlib import Path
import hashlib,json,re,subprocess
workspace=Path(__file__).resolve().parent.parent
source=Path('/root/hmos-work/gki-sheng-exports')
out=Path('/root/hmos-work/gki-out-sheng-exports')
baseout=Path('/root/hmos-work/gki-out-stock')
revision=subprocess.check_output(['git','-C',str(source),'rev-parse','HEAD'],text=True).strip()
assert revision=='6f2f96be86b93de6ed58a2c46b456fb49734c382'
helpers=re.findall(r'resolve_api\("([^"]+)"',(workspace/'compat/sheng-hmos-ipc/src/private_api.c').read_text())
existing={line.split()[1] for line in (baseout/'vmlinux.symvers').read_text().splitlines() if line.strip()}
assert len(helpers)==20
added=['sheng_hmos_ipc_api_v1']
header='''/* SPDX-License-Identifier: GPL-2.0 */
#ifndef SHENG_HMOS_API_V1_H
#define SHENG_HMOS_API_V1_H
#include <linux/cache.h>
#include <linux/list_lru.h>
#include <linux/poll.h>
#include <linux/fdtable.h>
#include <linux/capability.h>
#include <linux/sched/mm.h>
#include <linux/security.h>
#include <linux/task_work.h>
#include <linux/mm.h>
#define SHENG_HMOS_API_MAGIC 0x5348454e47495043ULL
struct sheng_hmos_ipc_api_v1 {
    u64 magic;
    u32 version;
    u32 size;
'''+''.join(f'    typeof({name}) *api_{name};\n' for name in helpers)+''' };
#endif
'''
shim='''// SPDX-License-Identifier: GPL-2.0
/* Read-only, typed CFI entry points for the isolated Harmony IPC module.
 * Function addresses are emitted by the C compiler as canonical jump-table
 * entries. Raw kallsyms/export implementation addresses are not used.
 * Original security/MM implementations and CFI enforcement remain intact. */
#include <linux/export.h>
#include "sheng_hmos_api_v1.h"
const struct sheng_hmos_ipc_api_v1 sheng_hmos_ipc_api_v1 = {
    .magic = SHENG_HMOS_API_MAGIC,
    .version = 1,
    .size = sizeof(struct sheng_hmos_ipc_api_v1),
'''+''.join(f'    .api_{name} = {name},\n' for name in helpers)+'''};
EXPORT_SYMBOL_GPL(sheng_hmos_ipc_api_v1);
'''
path=source/'drivers/android/sheng_hmos_exports.c'
if path.exists() and path.read_text()!=shim:
    previous=json.loads((workspace/'analysis/gki-sheng-exports-preparation.json').read_text())
    assert hashlib.sha256(path.read_bytes()).hexdigest()==previous['shim_sha256'], 'Preserve unexpected source edits'
path.write_text(shim)
(source/'drivers/android/sheng_hmos_api_v1.h').write_text(header)
shared=workspace/'compat/sheng-hmos-ipc/api/sheng_hmos_api_v1.h'
shared.parent.mkdir(exist_ok=True);shared.write_text(header)
makefile=source/'drivers/android/Makefile';before=makefile.read_text()
line='obj-y += sheng_hmos_exports.o\n'
if line not in before:makefile.write_text(before+line)
out.mkdir(exist_ok=True)
whitelist=out/'abi_symbollist.raw'
oldlist=(baseout/'abi_symbollist.raw').read_text().splitlines()
whitelist.write_text('\n'.join(sorted(set(oldlist+added)))+'\n')
config=(baseout/'.config').read_text()
config=re.sub(r'^CONFIG_UNUSED_KSYMS_WHITELIST=.*$',f'CONFIG_UNUSED_KSYMS_WHITELIST="{whitelist}"',config,flags=re.M)
target=out/'.config'
if target.exists():assert target.read_text()==config,'Preserve changed build configuration'
else:target.write_text(config)
(source/'.scmversion').write_text('-android13-8-00021-g6f2f96be86b9\n')
patch=subprocess.check_output(['git','-C',str(source),'diff','--','drivers/android/Makefile'],text=True)
(workspace/'analysis/gki-sheng-exports.patch').write_text(patch+'\nNew file: drivers/android/sheng_hmos_exports.c\n'+shim)
report={'source':revision,'added_gpl_exports':added,'config_change':'local whitelist path and appended export names only',
        'cfi':'CONFIG_CFI_CLANG=y; CONFIG_CFI_PERMISSIVE remains unset',
        'shim_sha256':hashlib.sha256(shim.encode()).hexdigest(),'typed_private_apis':helpers,'flashed':False}
(workspace/'analysis/gki-sheng-exports-preparation.json').write_text(json.dumps(report,indent=2))
print(json.dumps(report,indent=2))
