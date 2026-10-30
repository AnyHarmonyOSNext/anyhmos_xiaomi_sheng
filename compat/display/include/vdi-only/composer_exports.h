// Function signatures projected verbatim from the official VDI adapter.
#pragma once
#include "buffer_handle.h"
#include "display/composer/v1_3/display_composer_type.h"
#include "display_common.h"
namespace OHOS::HDI::Display::Composer {
using namespace OHOS::HDI::Display;
using namespace V1_0;
using namespace V1_1;
using namespace V1_2;
using namespace V1_3;
extern "C" int32_t LoadVdiImpl();
extern "C" int32_t DestroyVdiImpl();
extern "C" int32_t RegHotPlugCallback(HotPlugCallback cb, void* data);
extern "C" int32_t GetDisplayCapability(uint32_t devId, DisplayCapability& info);
extern "C" int32_t GetDisplaySupportedModes(uint32_t devId, std::vector<DisplayModeInfo>& modes);
extern "C" int32_t GetDisplayMode(uint32_t devId, uint32_t& modeId);
extern "C" int32_t SetDisplayMode(uint32_t devId, uint32_t modeId);
extern "C" int32_t GetDisplayPowerStatus(uint32_t devId, V1_0::DispPowerStatus& status);
extern "C" int32_t SetDisplayPowerStatus(uint32_t devId, V1_0::DispPowerStatus status);
extern "C" int32_t GetDisplayBacklight(uint32_t devId, uint32_t& level);
extern "C" int32_t SetDisplayBacklight(uint32_t devId, uint32_t level);
extern "C" int32_t GetDisplayProperty(uint32_t devId, uint32_t id, uint64_t& value);
extern "C" int32_t GetDisplayCompChange(uint32_t devId, std::vector<uint32_t>& layers, std::vector<int32_t>& types);
extern "C" int32_t SetDisplayClientCrop(uint32_t devId, const IRect& rect);
extern "C" int32_t SetDisplayClientBuffer(uint32_t devId, const BufferHandle& buffer, int32_t fence);
extern "C" int32_t SetDisplayClientDamage(uint32_t devId, std::vector<IRect>& rects);
extern "C" int32_t SetDisplayVsyncEnabled(uint32_t devId, bool enabled);
extern "C" int32_t RegDisplayVBlankCallback(uint32_t devId, VBlankCallback cb, void* data);
extern "C" int32_t GetDisplayReleaseFence(uint32_t devId, std::vector<uint32_t>& layers, std::vector<int32_t>& fences);
extern "C" int32_t CreateVirtualDisplay(uint32_t width, uint32_t height, int32_t& format, uint32_t& devId);
extern "C" int32_t DestroyVirtualDisplay(uint32_t devId);
extern "C" int32_t SetVirtualDisplayBuffer(uint32_t devId, const BufferHandle& buffer, const int32_t fence);
extern "C" int32_t SetDisplayProperty(uint32_t devId, uint32_t id, uint64_t value);
extern "C" int32_t Commit(uint32_t devId, int32_t& fence);
extern "C" int32_t CreateLayer(uint32_t devId, const LayerInfo& layerInfo, uint32_t& layerId);
extern "C" int32_t DestroyLayer(uint32_t devId, uint32_t layerId);
extern "C" int32_t PrepareDisplayLayers(uint32_t devId, bool& needFlushFb);
extern "C" int32_t SetLayerAlpha(uint32_t devId, uint32_t layerId, const LayerAlpha& alpha);
extern "C" int32_t SetLayerRegion(uint32_t devId, uint32_t layerId, const IRect& rect);
extern "C" int32_t SetLayerCrop(uint32_t devId, uint32_t layerId, const IRect& rect);
extern "C" int32_t SetLayerZorder(uint32_t devId, uint32_t layerId, uint32_t zorder);
extern "C" int32_t SetLayerPreMulti(uint32_t devId, uint32_t layerId, bool preMul);
extern "C" int32_t SetLayerTransformMode(uint32_t devId, uint32_t layerId, TransformType type);
extern "C" int32_t SetLayerDirtyRegion(uint32_t devId, uint32_t layerId, const std::vector<IRect>& rects);
extern "C" int32_t SetLayerVisibleRegion(uint32_t devId, uint32_t layerId, std::vector<IRect>& rects);
extern "C" int32_t SetLayerBuffer(uint32_t devId, uint32_t layerId, const BufferHandle& buffer, int32_t fence);
extern "C" int32_t SetLayerCompositionType(uint32_t devId, uint32_t layerId, V1_0::CompositionType type);
extern "C" int32_t SetLayerBlendType(uint32_t devId, uint32_t layerId, BlendType type);
extern "C" int32_t SetLayerMaskInfo(uint32_t devId, uint32_t layerId, const MaskInfo maskInfo);
extern "C" int32_t SetLayerColor(uint32_t devId, uint32_t layerId, const LayerColor& layerColor);
extern "C" int32_t RegSeamlessChangeCallback(SeamlessChangeCallback cb, void* data);
extern "C" int32_t GetDisplaySupportedModesExt(uint32_t devId, std::vector<DisplayModeInfoExt>& modes);
extern "C" int32_t SetDisplayModeAsync(uint32_t devId, uint32_t modeId, ModeCallback cb, void *data);
extern "C" int32_t GetDisplayVBlankPeriod(uint32_t devId, uint64_t& period);
extern "C" int32_t SetLayerPerFrameParameter(
        uint32_t devId, uint32_t layerId, const std::string& key, const std::vector<int8_t>& value);
extern "C" int32_t SetDisplayPerFrameParameter(
        uint32_t devId, const std::string& key, const std::vector<int8_t>& value);
extern "C" int32_t GetSupportedLayerPerFrameParameterKey(std::vector<std::string>& keys);
extern "C" int32_t SetDisplayOverlayResolution(uint32_t devId, uint32_t width, uint32_t height);
extern "C" int32_t RegRefreshCallback(RefreshCallback cb, void* data);
extern "C" int32_t GetDisplaySupportedColorGamuts(uint32_t devId, std::vector<ColorGamut>& gamuts);
extern "C" int32_t GetHDRCapabilityInfos(uint32_t devId, HDRCapability& info);
extern "C" int32_t RegDisplayVBlankIdleCallback(VBlankIdleCallback cb, void* data);
extern "C" int32_t SetDisplayConstraint(uint32_t devId, uint64_t frameID, uint64_t ns, uint32_t type);
extern "C" int32_t UpdateHardwareCursor(uint32_t devId, int32_t x, int32_t y, BufferHandle* buffer);
extern "C" int32_t EnableHardwareCursorStats(uint32_t devId, bool enable);
extern "C" int32_t GetHardwareCursorStats(uint32_t devId, uint32_t& frameCount, uint32_t& vsyncCount);
extern "C" int32_t SetDisplayActiveRegion(uint32_t devId, const IRect& rect);
extern "C" int32_t FastPresent(uint32_t devId, const PresentParam& param,
        const std::vector<BufferHandle*>& inHandles);
extern "C" int32_t ClearDisplayClientBuffer(uint32_t devId);
extern "C" int32_t ClearLayerBuffer(uint32_t devId, uint32_t layerId);
extern "C" int32_t GetDisplayIdentificationData(uint32_t devId, uint8_t& portId, std::vector<uint8_t>& edidData);
extern "C" int32_t RegHwcEventCallback(HwcEventCallback cb, void *data);
}
