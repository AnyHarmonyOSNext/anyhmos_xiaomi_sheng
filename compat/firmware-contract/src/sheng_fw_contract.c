// Read-only firmware-loader contract. No device is powered or registered.
#include <linux/module.h>
#include <linux/firmware.h>
#include <linux/string.h>

static char *name = "sheng-fw-contract-regular.bin";
module_param(name, charp, 0400);
static int result = -EINPROGRESS;
module_param(result, int, 0400);
static unsigned long bytes;
module_param(bytes, ulong, 0400);

static int __init sheng_fw_contract_init(void)
{
    const struct firmware *fw = NULL;
    if (strcmp(name, "sheng-fw-contract-regular.bin") &&
        strcmp(name, "sheng-fw-contract-link.bin") &&
        strcmp(name, "adsp.mdt") && strcmp(name, "kiwi/amss20.bin"))
        return -EINVAL;
    result = request_firmware_direct(&fw, name, NULL);
    if (!result) {
        bytes = fw->size;
        release_firmware(fw);
    }
    pr_info("SHENG_FW_CONTRACT name=%s result=%d bytes=%lu\n", name, result, bytes);
    // Keep the result readable even if the firmware request failed.
    return 0;
}

static void __exit sheng_fw_contract_exit(void) {}
module_init(sheng_fw_contract_init);
module_exit(sheng_fw_contract_exit);
MODULE_LICENSE("GPL");
MODULE_DESCRIPTION("Sheng read-only firmware-loader path diagnostic");
