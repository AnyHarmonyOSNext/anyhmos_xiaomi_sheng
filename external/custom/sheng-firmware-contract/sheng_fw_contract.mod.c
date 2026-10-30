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
	{ 0xefc8860a, "param_ops_ulong" },
	{ 0x65cafe5c, "param_ops_int" },
	{ 0x3fa768fd, "param_ops_charp" },
	{ 0xdf7a4c69, "__ubsan_handle_cfi_check_fail_abort" },
	{ 0x92997ed8, "_printk" },
	{ 0xc6d09aa9, "release_firmware" },
	{ 0x12a49c27, "request_firmware_direct" },
	{ 0xe2d5255a, "strcmp" },
};

MODULE_INFO(depends, "");

