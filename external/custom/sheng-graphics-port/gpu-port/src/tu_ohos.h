/* SPDX-License-Identifier: MIT
 * Ace5 linear DMA-BUF bridge for the pinned HarmonyOS native-buffer ABI.
 */
#ifndef TU_OHOS_H
#define TU_OHOS_H
#include <stdint.h>
#include <vulkan/vulkan.h>
struct Ace5OHBufferHandle {
 int32_t fd, width, stride, height, size, format;
 uint64_t usage;
 void *virAddr;
 uint64_t phyAddr;
 uint32_t reserveFds, reserveInts;
};
extern "C" {
const Ace5OHBufferHandle *OH_NativeBuffer_GetBufferHandle(const OH_NativeBuffer *);
int32_t OH_NativeBuffer_Reference(OH_NativeBuffer *);
int32_t OH_NativeBuffer_Unreference(OH_NativeBuffer *);
}
struct tu_device;
struct tu_image;
bool tu_ohos_valid_handle(const Ace5OHBufferHandle *);
bool tu_ohos_supported_format(VkFormat);
VkResult tu_ohos_bind_layout(tu_device *,tu_image *,const Ace5OHBufferHandle *);
VkResult tu_ohos_import_image(tu_device *,tu_image *,const VkNativeBufferOHOS *,const VkAllocationCallbacks *);
#endif
