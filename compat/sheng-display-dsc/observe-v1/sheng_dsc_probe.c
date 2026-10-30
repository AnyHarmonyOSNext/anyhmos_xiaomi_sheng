// SPDX-License-Identifier: GPL-2.0-only
/* Read-only DSC call observation for the explicitly staged sheng trial.
 * Normal kprobe callbacks only; no private function calls, MMIO writes,
 * parameter changes, forced module loading, or CFI disablement.
 */
#include <linux/module.h>
#include <linux/kprobes.h>
#include <linux/uaccess.h>
#include <linux/atomic.h>
#include <drm/drm_dsc.h>

static atomic_t observations = ATOMIC_INIT(0);
static int observe_config(struct kprobe *probe, struct pt_regs *regs)
{
    struct drm_dsc_config config;
    unsigned long address = regs->regs[1];
    int count = atomic_inc_return(&observations);

    if (count > 32)
        return 0;
    if (copy_from_kernel_nofault(&config, (const void *)address, sizeof(config))) {
        pr_info("SHENG_DSC_OBSERVE unreadable count=%d symbol=%s\n", count, probe->symbol_name);
        return 0;
    }
    pr_info("SHENG_DSC_OBSERVE count=%d symbol=%s cfg_bytes=%zu mode=%lx bpc=%u bpp=%u pic=%ux%u slice=%ux%u slices=%u rgb=%u version=%u.%u\n",
        count, probe->symbol_name, sizeof(config), regs->regs[2],
        config.bits_per_component, config.bits_per_pixel,
        config.pic_width, config.pic_height, config.slice_width, config.slice_height,
        config.slice_count, config.convert_rgb, config.dsc_version_major, config.dsc_version_minor);
    return 0;
}

static struct kprobe probes[] = {
    { .symbol_name = "msm_drm:sde_hw_dsc_config.9bb27182427be83f7532ee7d54d33807", .pre_handler = observe_config },
    { .symbol_name = "msm_drm:sde_hw_dsc_config.b46e25d6a9148e14877c4a661eeda8be", .pre_handler = observe_config },
};
static unsigned int registered;

static int __init sheng_dsc_probe_init(void)
{
    int result;
    for (registered = 0; registered < ARRAY_SIZE(probes); registered++) {
        result = register_kprobe(&probes[registered]);
        if (result) {
            pr_err("SHENG_DSC_OBSERVE register failed index=%u result=%d\n", registered, result);
            while (registered)
                unregister_kprobe(&probes[--registered]);
            return result;
        }
    }
    pr_info("SHENG_DSC_OBSERVE loaded read_only=1 probes=%u cfg_bytes=%zu\n", registered, sizeof(struct drm_dsc_config));
    return 0;
}
static void __exit sheng_dsc_probe_exit(void)
{
    while (registered)
        unregister_kprobe(&probes[--registered]);
    pr_info("SHENG_DSC_OBSERVE unloaded observations=%d\n", atomic_read(&observations));
}
module_init(sheng_dsc_probe_init);
module_exit(sheng_dsc_probe_exit);
MODULE_LICENSE("GPL");
MODULE_DESCRIPTION("Read-only sheng DSC parameter observation");
MODULE_AUTHOR("Sheng port diagnostic work");
