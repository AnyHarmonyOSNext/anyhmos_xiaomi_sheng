// SPDX-License-Identifier: GPL-2.0-only
/* DSC observation / opt-in sheng dual-DSI parameter correction.
 * Normal kprobe callbacks; the original driver programs the hardware.
 * Default is observation only. The correction is gated to the verified
 * 3048x2032 n81a geometry and this exact vendor DSC 1.2 implementation.
 */
#include <linux/module.h>
#include <linux/kprobes.h>
#include <linux/uaccess.h>
#include <linux/atomic.h>
#include <drm/drm_dsc.h>

static atomic_t observations = ATOMIC_INIT(0);
static atomic_t corrections = ATOMIC_INIT(0);
static struct kprobe probes[2];
static bool enable_fix;
module_param(enable_fix, bool, 0444);
MODULE_PARM_DESC(enable_fix, "Opt-in n81a dual-DSI picture-width and split-mode correction");
static int observe_config(struct kprobe *probe, struct pt_regs *regs)
{
    struct drm_dsc_config config;
    unsigned long address = regs->regs[1];
    int count = atomic_inc_return(&observations);

    if (copy_from_kernel_nofault(&config, (const void *)address, sizeof(config))) {
        if (count <= 32)
            pr_info("SHENG_DSC_OBSERVE unreadable count=%d symbol=%s\n", count, probe->symbol_name);
        return 0;
    }
    if (enable_fix && probe == &probes[1] &&
        config.bits_per_component == 8 && config.bits_per_pixel == 128 &&
        config.dsc_version_major == 1 && config.dsc_version_minor == 1 &&
        config.pic_height == 2032 && (config.pic_width == 3048 || config.pic_width == 1524) &&
        config.slice_width == 762 && config.slice_height == 16 && config.slice_count == 2 &&
        config.convert_rgb && config.initial_xmit_delay == 512 && regs->regs[2] == 5) {
        struct drm_dsc_config *live = (struct drm_dsc_config *)address;
        int fixed = atomic_inc_return(&corrections);
        /* One independent compressed picture per physical DSI interface.
         * Clear DSC_MODE_SPLIT_PANEL, retain DSC_MODE_VIDEO. No function
         * address calls or instruction-pointer redirection are used.
         */
        WRITE_ONCE(live->pic_width, 1524);
        regs->regs[2] = 4;
        if (fixed <= 32)
            pr_info("SHENG_DSC_FIX applied=%d pic=%u->1524 height=2032 mode=5->4\n", fixed, config.pic_width);
    }
    if (count > 32)
        return 0;
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
    pr_info("SHENG_DSC_OBSERVE loaded enable_fix=%u probes=%u cfg_bytes=%zu\n", enable_fix, registered, sizeof(struct drm_dsc_config));
    return 0;
}
static void __exit sheng_dsc_probe_exit(void)
{
    while (registered)
        unregister_kprobe(&probes[--registered]);
    pr_info("SHENG_DSC_OBSERVE unloaded observations=%d corrections=%d\n", atomic_read(&observations), atomic_read(&corrections));
}
module_init(sheng_dsc_probe_init);
module_exit(sheng_dsc_probe_exit);
MODULE_LICENSE("GPL");
MODULE_DESCRIPTION("Sheng DSC observation and opt-in n81a dual-DSI correction");
MODULE_AUTHOR("Sheng port diagnostic work");
