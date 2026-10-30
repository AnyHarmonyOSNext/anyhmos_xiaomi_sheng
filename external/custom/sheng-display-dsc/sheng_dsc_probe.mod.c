#include <linux/module.h>
#define INCLUDE_VERMAGIC
#include <linux/build-salt.h>
#include <linux/elfnote-lto.h>
#include <linux/vermagic.h>
#include <linux/compiler.h>

BUILD_SALT;
BUILD_LTO_INFO;

MODULE_INFO(vermagic, VERMAGIC_STRING);
MODULE_INFO(name, KBUILD_MODNAME);

__visible struct module __this_module
__section(".gnu.linkonce.this_module") = {
	.name = KBUILD_MODNAME,
	.init = init_module,
#ifdef CONFIG_MODULE_UNLOAD
	.exit = cleanup_module,
#endif
	.arch = MODULE_ARCH_INIT,
};

#ifdef CONFIG_RETPOLINE
MODULE_INFO(retpoline, "Y");
#endif

static const struct modversion_info ____versions[]
__used __section("__versions") = {
	{ 0x222dd63, "module_layout" },
	{ 0xc2c193d2, "__stack_chk_fail" },
	{ 0xd14fef22, "cpu_hwcap_keys" },
	{ 0x14b89635, "arm64_const_caps_ready" },
	{ 0x8070288, "param_ops_bool" },
	{ 0xdf7a4c69, "__ubsan_handle_cfi_check_fail_abort" },
	{ 0x4531ab62, "copy_from_kernel_nofault" },
	{ 0xeb78b1ed, "unregister_kprobe" },
	{ 0x92997ed8, "_printk" },
	{ 0x472cf3b, "register_kprobe" },
};

MODULE_INFO(depends, "");

