#include "composer_exports.h"
namespace OHOS::HDI::Display::Composer {
extern "C" int32_t GetDisplayProperty(uint32_t devId, uint32_t id, uint64_t& value) { return -5; }
extern "C" int32_t CreateVirtualDisplay(uint32_t width, uint32_t height, int32_t& format, uint32_t& devId) { return -5; }
extern "C" int32_t DestroyVirtualDisplay(uint32_t devId) { return -5; }
extern "C" int32_t SetVirtualDisplayBuffer(uint32_t devId, const BufferHandle& buffer, const int32_t fence) { return -5; }
extern "C" int32_t SetDisplayProperty(uint32_t devId, uint32_t id, uint64_t value) { return -5; }
extern "C" int32_t RegSeamlessChangeCallback(SeamlessChangeCallback cb, void* data) { return -5; }
extern "C" int32_t SetDisplayModeAsync(uint32_t devId, uint32_t modeId, ModeCallback cb, void *data) { return -5; }
extern "C" int32_t SetLayerPerFrameParameter(
        uint32_t devId, uint32_t layerId, const std::string& key, const std::vector<int8_t>& value) { return -5; }
extern "C" int32_t SetDisplayPerFrameParameter(
        uint32_t devId, const std::string& key, const std::vector<int8_t>& value) { return -5; }
extern "C" int32_t GetSupportedLayerPerFrameParameterKey(std::vector<std::string>& keys) { return -5; }
extern "C" int32_t SetDisplayOverlayResolution(uint32_t devId, uint32_t width, uint32_t height) { return -5; }
extern "C" int32_t RegRefreshCallback(RefreshCallback cb, void* data) { return -5; }
extern "C" int32_t GetDisplaySupportedColorGamuts(uint32_t devId, std::vector<ColorGamut>& gamuts) { return -5; }
extern "C" int32_t GetHDRCapabilityInfos(uint32_t devId, HDRCapability& info) { return -5; }
extern "C" int32_t RegDisplayVBlankIdleCallback(VBlankIdleCallback cb, void* data) { return -5; }
extern "C" int32_t SetDisplayConstraint(uint32_t devId, uint64_t frameID, uint64_t ns, uint32_t type) { return -5; }
extern "C" int32_t UpdateHardwareCursor(uint32_t devId, int32_t x, int32_t y, BufferHandle* buffer) { return -5; }
extern "C" int32_t EnableHardwareCursorStats(uint32_t devId, bool enable) { return -5; }
extern "C" int32_t GetHardwareCursorStats(uint32_t devId, uint32_t& frameCount, uint32_t& vsyncCount) { return -5; }
extern "C" int32_t SetDisplayActiveRegion(uint32_t devId, const IRect& rect) { return -5; }
extern "C" int32_t FastPresent(uint32_t devId, const PresentParam& param,
        const std::vector<BufferHandle*>& inHandles) { return -5; }
extern "C" int32_t GetDisplayIdentificationData(uint32_t devId, uint8_t& portId, std::vector<uint8_t>& edidData) { return -5; }
extern "C" int32_t RegHwcEventCallback(HwcEventCallback cb, void *data) { return -5; }
}
