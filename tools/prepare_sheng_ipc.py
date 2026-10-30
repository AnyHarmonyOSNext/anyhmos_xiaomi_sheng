"""Run in WSL. Apply explicit API backports to the isolated reference copy."""
from pathlib import Path
import difflib
import hashlib
import json
import shutil

workspace = Path(__file__).resolve().parent.parent
ref = Path('/root/hmos-reference/AnyHarmonyOS/sm8650/kernel-port/driver-module')
target = Path('/root/hmos-work/sheng-hmos-ipc')
target.mkdir(exist_ok=True)
patches = []
for source in ref.iterdir():
    if not source.is_file():
        continue
    dest = target/source.name
    if not dest.exists():
        shutil.copyfile(source, dest)
source = ref/'binder_alloc.c'
before = source.read_text()
old, new = 'register_shrinker(&binder_shrinker, "android-binder")', 'register_shrinker(&binder_shrinker)'
assert before.count(old) == 1
after = before.replace(old, new)
dest = target/source.name
assert dest.read_text() in (before, after), 'Preserve unexpected local edits and review them.'
dest.write_text(after)
patches.extend(difflib.unified_diff(before.splitlines(True), after.splitlines(True), fromfile='reference/binder_alloc.c', tofile='sheng/binder_alloc.c'))
source = ref/'Makefile'
before = source.read_text()
after = before.replace('ace5_hmos_ipc', 'sheng_hmos_ipc')
dest = target/source.name
assert dest.read_text() in (before, after)
dest.write_text(after)
patches.extend(difflib.unified_diff(before.splitlines(True), after.splitlines(True), fromfile='reference/Makefile', tofile='sheng/Makefile'))
for name, old, new in [
    ('binder.c', '#include <linux/cacheflush.h>', '#include <asm/cacheflush.h>'),
    ('private_api.h', '#include <linux/list_lru.h>', '#include <linux/cache.h>\n#include <linux/list_lru.h>'),
    ('hmos_config.h', '#undef CONFIG_ANDROID_BINDERFS', '''#undef CONFIG_ANDROID_BINDERFS
/* Linux 6.1 Binder extension, local to this module on stock 5.15.
 * Layout/command from include/uapi/linux/android/binder.h, GPL-2.0 WITH
 * Linux-syscall-note. No stock kernel UAPI or task structure is changed. */
#include <uapi/linux/android/binder.h>
#ifndef BINDER_GET_EXTENDED_ERROR
struct binder_extended_error {
    __u32 id;
    __u32 command;
    __s32 param;
};
#define BINDER_GET_EXTENDED_ERROR _IOWR('b', 17, struct binder_extended_error)
#endif''')]:
    source = ref/name
    before = source.read_text()
    assert before.count(old) == 1
    after = before.replace(old, new)
    previous_after = after
    if name == 'binder.c':
        edits = [
            ('twcb->file = close_fd_get_file(fd);', 'close_fd_get_file(fd, &twcb->file);'),
            ('\t\t// pin it until binder_do_fd_close(); see comments there\n\t\tget_file(twcb->file);\n', ''),
            ('TASK_INTERRUPTIBLE|TASK_FREEZABLE', 'TASK_INTERRUPTIBLE'),
            ('\tvm_flags_mod(vma, VM_DONTCOPY | VM_MIXEDMAP, VM_MAYWRITE);', '\tvma->vm_flags = (vma->vm_flags | VM_DONTCOPY | VM_MIXEDMAP) & ~VM_MAYWRITE;'),
            ('\tint ret = 0;\n\n\tbinder_inner_proc_lock(proc);\n\tfor (;;) {\n\t\tprepare_to_wait', '\tint ret = 0;\n\n\tfreezer_do_not_count();\n\tbinder_inner_proc_lock(proc);\n\tfor (;;) {\n\t\tprepare_to_wait'),
            ('\tfinish_wait(&thread->wait, &wait);\n\tbinder_inner_proc_unlock(proc);\n', '\tfinish_wait(&thread->wait, &wait);\n\tbinder_inner_proc_unlock(proc);\n\tfreezer_count();\n')
        ]
        for oldpart, newpart in edits:
            assert after.count(oldpart) == 1, oldpart
            after = after.replace(oldpart, newpart)
    dest = target/name
    assert dest.read_text() in (before, previous_after, after), name
    dest.write_text(after)
    patches.extend(difflib.unified_diff(before.splitlines(True), after.splitlines(True), fromfile='reference/'+name, tofile='sheng/'+name))
(workspace/'analysis/sheng-ipc-backport.patch').write_text(''.join(patches))
manifest = {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(ref.iterdir()) if p.is_file()}
(workspace/'analysis/sheng-ipc-reference-sha256.json').write_text(json.dumps({'source_commit': 'cb1ce16', 'files': manifest}, indent=2))
print('Isolated copy prepared. Reference repository unchanged. Compile/device tests still required.')
