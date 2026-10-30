#define ACE5_PRIVATE_IMPLEMENTATION
#include "private_api.h"
#include <linux/kprobes.h>
#include <linux/delay.h>
typeof(__list_lru_init) *ace5_api___list_lru_init;
typeof(__wake_up_pollfree) *ace5_api___wake_up_pollfree;
typeof(close_fd_get_file) *ace5_api_close_fd_get_file;
typeof(has_capability_noaudit) *ace5_api_has_capability_noaudit;
typeof(list_lru_add) *ace5_api_list_lru_add;
typeof(list_lru_count_node) *ace5_api_list_lru_count_node;
typeof(list_lru_del) *ace5_api_list_lru_del;
typeof(list_lru_destroy) *ace5_api_list_lru_destroy;
typeof(list_lru_isolate) *ace5_api_list_lru_isolate;
typeof(list_lru_walk_node) *ace5_api_list_lru_walk_node;
typeof(mmput_async) *ace5_api_mmput_async;
typeof(security_binder_set_context_mgr) *ace5_api_security_binder_set_context_mgr;
typeof(security_binder_transaction) *ace5_api_security_binder_transaction;
typeof(security_binder_transfer_binder) *ace5_api_security_binder_transfer_binder;
typeof(security_binder_transfer_file) *ace5_api_security_binder_transfer_file;
typeof(security_cred_getsecid) *ace5_api_security_cred_getsecid;
typeof(security_release_secctx) *ace5_api_security_release_secctx;
typeof(security_secid_to_secctx) *ace5_api_security_secid_to_secctx;
typeof(task_work_add) *ace5_api_task_work_add;
typeof(zap_page_range) *ace5_api_zap_page_range;
static int resolve_api(const char *name, void **result)
{
    struct kprobe probe = { .symbol_name = name };
    int ret;
    pr_info("SHENG_IPC resolve-begin name=%s\n", name);
    msleep(100);
    ret = register_kprobe(&probe);
    pr_info("SHENG_IPC resolve-result name=%s ret=%d address=%px\n", name, ret, probe.addr);
    msleep(100);
    if (ret) { pr_err("ACE5_TOKEN: required kernel API %s unavailable: %d\n", name, ret); return ret; }
    *result = (void *)probe.addr;
    unregister_kprobe(&probe);
    pr_info("SHENG_IPC resolve-done name=%s\n", name);
    msleep(100);
    return 0;
}
int ace5_private_api_init(void)
{
    int ret;
    ret = resolve_api("__list_lru_init", (void **)&ace5_api___list_lru_init);
    if (ret) return ret;
    ret = resolve_api("__wake_up_pollfree", (void **)&ace5_api___wake_up_pollfree);
    if (ret) return ret;
    ret = resolve_api("close_fd_get_file", (void **)&ace5_api_close_fd_get_file);
    if (ret) return ret;
    ret = resolve_api("has_capability_noaudit", (void **)&ace5_api_has_capability_noaudit);
    if (ret) return ret;
    ret = resolve_api("list_lru_add", (void **)&ace5_api_list_lru_add);
    if (ret) return ret;
    ret = resolve_api("list_lru_count_node", (void **)&ace5_api_list_lru_count_node);
    if (ret) return ret;
    ret = resolve_api("list_lru_del", (void **)&ace5_api_list_lru_del);
    if (ret) return ret;
    ret = resolve_api("list_lru_destroy", (void **)&ace5_api_list_lru_destroy);
    if (ret) return ret;
    ret = resolve_api("list_lru_isolate", (void **)&ace5_api_list_lru_isolate);
    if (ret) return ret;
    ret = resolve_api("list_lru_walk_node", (void **)&ace5_api_list_lru_walk_node);
    if (ret) return ret;
    ret = resolve_api("mmput_async", (void **)&ace5_api_mmput_async);
    if (ret) return ret;
    ret = resolve_api("security_binder_set_context_mgr", (void **)&ace5_api_security_binder_set_context_mgr);
    if (ret) return ret;
    ret = resolve_api("security_binder_transaction", (void **)&ace5_api_security_binder_transaction);
    if (ret) return ret;
    ret = resolve_api("security_binder_transfer_binder", (void **)&ace5_api_security_binder_transfer_binder);
    if (ret) return ret;
    ret = resolve_api("security_binder_transfer_file", (void **)&ace5_api_security_binder_transfer_file);
    if (ret) return ret;
    ret = resolve_api("security_cred_getsecid", (void **)&ace5_api_security_cred_getsecid);
    if (ret) return ret;
    ret = resolve_api("security_release_secctx", (void **)&ace5_api_security_release_secctx);
    if (ret) return ret;
    ret = resolve_api("security_secid_to_secctx", (void **)&ace5_api_security_secid_to_secctx);
    if (ret) return ret;
    ret = resolve_api("task_work_add", (void **)&ace5_api_task_work_add);
    if (ret) return ret;
    ret = resolve_api("zap_page_range", (void **)&ace5_api_zap_page_range);
    if (ret) return ret;
    return 0;
}

/* Header inline helpers call these names before the alias macros apply. */
void __wake_up_pollfree(struct wait_queue_head *head)
{ ace5_api___wake_up_pollfree(head); }
unsigned long list_lru_count_node(struct list_lru *lru, int nid)
{ return ace5_api_list_lru_count_node(lru, nid); }
unsigned long list_lru_walk_node(struct list_lru *lru, int nid,
    list_lru_walk_cb isolate, void *arg, unsigned long *nr)
{ return ace5_api_list_lru_walk_node(lru, nid, isolate, arg, nr); }
