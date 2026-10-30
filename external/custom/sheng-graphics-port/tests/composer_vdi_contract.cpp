#include "composer_exports.h"
#include "idisplay_buffer_vdi.h"
#include <atomic>
#include <cstdio>
#include <cstring>
#include <dlfcn.h>
#include <unistd.h>
namespace C = OHOS::HDI::Display::Composer;
namespace B = OHOS::HDI::Display::Buffer::V1_0;
#define CHECK(x) do { if (!(x)) { printf("FAIL line=%d: %s\n", __LINE__, #x); return 1; } } while (0)
#define LOAD(name) auto name = reinterpret_cast<decltype(&C::name)>(dlsym(composer, #name)); CHECK(name)
static bool connected;
static std::atomic<unsigned> vsyncCount{0};
static void Hotplug(uint32_t id, bool online, void *) { connected = id == 0 && online; }
static void Vsync(unsigned, uint64_t ns, void *) { if (ns) ++vsyncCount; }
int main(int argc, char **argv)
{
    setbuf(stdout, nullptr); alarm(20); CHECK(argc == 3);
    auto *composer = dlopen(argv[1], RTLD_NOW | RTLD_LOCAL);
    if (!composer) { puts(dlerror()); return 1; }
    auto *allocator = dlopen(argv[2], RTLD_NOW | RTLD_LOCAL);
    if (!allocator) { puts(dlerror()); return 1; }
    LOAD(RegHotPlugCallback); LOAD(GetDisplayCapability); LOAD(GetDisplaySupportedModes);
    LOAD(GetDisplayMode); LOAD(CreateLayer); LOAD(DestroyLayer); LOAD(SetLayerCompositionType);
    LOAD(GetDisplayPowerStatus);
    LOAD(GetDisplayCompChange); LOAD(SetDisplayClientBuffer); LOAD(SetDisplayClientCrop);
    LOAD(RegDisplayVBlankCallback); LOAD(SetDisplayVsyncEnabled); LOAD(DestroyVdiImpl);
    auto test = reinterpret_cast<int32_t(*)(uint32_t)>(dlsym(composer, "Ace5TestClientBuffer")); CHECK(test);
    CHECK(RegHotPlugCallback(Hotplug, nullptr) == 0 && connected);
    C::V1_0::DispPowerStatus power;
    CHECK(GetDisplayPowerStatus(0, power) == 0);
    printf("REAL_POWER state=%d\n", int(power));
    C::V1_0::DisplayCapability capability{};
    CHECK(GetDisplayCapability(0, capability) == 0);
    CHECK(capability.name == "Sheng DSI" && capability.supportLayers == 64);
    std::vector<C::V1_0::DisplayModeInfo> modes;
    CHECK(GetDisplaySupportedModes(0, modes) == 0 && modes.size() == 1);
    auto m = modes[0];
    printf("REAL_SCREEN %dx%d@%u mm=%ux%u\n", m.width, m.height, m.freshRate, capability.phyWidth, capability.phyHeight);
    uint32_t layer;
    C::V1_0::LayerInfo info{m.width,m.height,C::V1_0::LAYER_TYPE_GRAPHIC,32,C::V1_0::PIXEL_FMT_RGBA_8888};
    CHECK(CreateLayer(0, info, layer) == 0);
    CHECK(SetLayerCompositionType(0, layer, C::V1_0::COMPOSITION_DEVICE) == 0);
    std::vector<uint32_t> ids; std::vector<int32_t> types;
    CHECK(GetDisplayCompChange(0, ids, types) == 0 && ids.size() == 1 && ids[0] == layer && types[0] == 0);
    auto create = reinterpret_cast<B::CreateDisplayBufferVdiFunc>(dlsym(allocator, "CreateDisplayBufferVdi"));
    auto destroy = reinterpret_cast<B::DestroyDisplayBufferVdiFunc>(dlsym(allocator, "DestroyDisplayBufferVdi"));
    CHECK(create && destroy); auto *vdi = create(); CHECK(vdi);
    BufferHandle *buffer = nullptr;
    CHECK(vdi->AllocMem({uint32_t(m.width),uint32_t(m.height),3 | (1ULL << 10),12,0}, buffer) == 0);
    CHECK(SetDisplayClientCrop(0, {0,0,m.width,m.height}) == 0);
    CHECK(SetDisplayClientBuffer(0, *buffer, -1) == 0);
    CHECK(test(0) == 0); // No modeset or visible frame is committed in recovery.
    CHECK(RegDisplayVBlankCallback(0, Vsync, nullptr) == 0);
    CHECK(SetDisplayVsyncEnabled(0, true) == 0); usleep(120000);
    CHECK(vsyncCount.load() >= 2);
    CHECK(SetDisplayVsyncEnabled(0, false) == 0);
    CHECK(DestroyLayer(0, layer) == 0);
    vdi->FreeMem(*buffer); destroy(vdi);
    CHECK(DestroyVdiImpl() == 0);
    dlclose(composer); dlclose(allocator);
    printf("COMPOSER_VDI_CONTRACT_RESULT=0 actual_atomic_test=1 software_vsync=%u\n", vsyncCount.load());
}
