"""Instrument only the isolated module copy; retain the v14 source baseline."""
from pathlib import Path
import difflib
workspace=Path(__file__).resolve().parent.parent
baseline=workspace/'compat/sheng-hmos-ipc/src'
target=Path('/root/hmos-work/sheng-hmos-ipc')
changes=[]
for name in ['ace5_tokens.c','private_api.c']:
    before=(baseline/name).read_text()
    after=before
    if name=='ace5_tokens.c':
        after=after.replace('#include <linux/module.h>', '#include <linux/module.h>\n#include <linux/delay.h>\nstatic int diagnostic_stage = -1;\nmodule_param(diagnostic_stage, int, 0400);')
        after=after.replace('    ret = ace5_private_api_init();', '''    pr_info("SHENG_IPC init-entry diagnostic_stage=%d\\n", diagnostic_stage);
    msleep(150);
    if (diagnostic_stage == 0) return -ECANCELED;
    pr_info("SHENG_IPC private-api-begin\\n");
    msleep(150);
    ret = ace5_private_api_init();
    pr_info("SHENG_IPC private-api-end ret=%d\\n", ret);''')
        after=after.replace('    for_each_kernel_tracepoint(find_hook, NULL);', '''    if (diagnostic_stage == 1) return -ECANCELED;
    pr_info("SHENG_IPC enumerate-hooks-begin\\n");
    msleep(150);
    for_each_kernel_tracepoint(find_hook, NULL);
    pr_info("SHENG_IPC enumerate-hooks-end\\n");''')
        after=after.replace('    for (i = 0; i < ARRAY_SIZE(hooks); i++) {\n        ret = tracepoint_probe_register', '''    if (diagnostic_stage == 2) return -ECANCELED;
    for (i = 0; i < ARRAY_SIZE(hooks); i++) {
        pr_info("SHENG_IPC register-hook index=%u name=%s\\n", i, hooks[i].name);
        msleep(150);
        ret = tracepoint_probe_register''')
        after=after.replace('    ret = ace5_token_device_init();', '''    pr_info("SHENG_IPC register-hooks-complete\\n");
    msleep(150);
    if (diagnostic_stage == 3) {
        unregister_hooks(ARRAY_SIZE(hooks));
        pr_info("SHENG_IPC diagnostic hooks removed\\n");
        return -ECANCELED;
    }
    pr_info("SHENG_IPC token-device-begin\\n");
    msleep(150);
    ret = ace5_token_device_init();
    pr_info("SHENG_IPC token-device-end ret=%d\\n", ret);''')
        after=after.replace('    ret = ace5_binder_init();', '''    pr_info("SHENG_IPC binder-begin\\n");
    msleep(150);
    ret = ace5_binder_init();
    pr_info("SHENG_IPC binder-end ret=%d\\n", ret);''')
    else:
        after=after.replace('#include <linux/kprobes.h>', '#include <linux/kprobes.h>\n#include <linux/delay.h>')
        after=after.replace('    int ret = register_kprobe(&probe);', '''    int ret;
    pr_info("SHENG_IPC resolve-begin name=%s\\n", name);
    msleep(100);
    ret = register_kprobe(&probe);
    pr_info("SHENG_IPC resolve-result name=%s ret=%d address=%px\\n", name, ret, probe.addr);
    msleep(100);''')
        after=after.replace('    unregister_kprobe(&probe);', '''    unregister_kprobe(&probe);
    pr_info("SHENG_IPC resolve-done name=%s\\n", name);
    msleep(100);''')
    assert before != after
    path=target/name
    assert path.read_text() in (before,after), 'Unexpected changes: '+name
    path.write_text(after)
    changes.extend(difflib.unified_diff(before.splitlines(True),after.splitlines(True),fromfile='v14/'+name,tofile='v15/'+name))
(workspace/'analysis/sheng-ipc-v15-instrumentation.patch').write_text(''.join(changes))
print('Diagnostic stage 0..3 cancel cleanly; -1 runs full initialization.')
