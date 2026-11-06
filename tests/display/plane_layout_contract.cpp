#include "idisplay_buffer_vdi.h"
#include <cstdio>
#include <cstdint>
#include <vector>

using namespace OHOS::HDI::Display::Buffer;

#define CHECK(condition) do { if (!(condition)) { \
    std::printf("PLANE_CONTRACT_FAIL line=%d expression=%s\n", __LINE__, #condition); \
    return 1; } } while (0)

struct ExpectedPlane {
    uint32_t offset, rowStride, columnStride, width, height;
};

int main()
{
    auto *vdi = V1_0::CreateDisplayBufferVdi();
    CHECK(vdi);
    unsigned cases = 0;
    auto checkLayout = [&](uint32_t format, uint32_t width, uint32_t height,
        uint32_t stride, uint32_t size, const std::vector<ExpectedPlane> &expected) {
        BufferHandle handle{};
        handle.fd = 0;
        handle.width = width;
        handle.height = height;
        handle.format = format;
        handle.stride = stride;
        handle.size = size;
        handle.usage = 9;
        V1_2::ImageLayout layout{};
        CHECK(vdi->GetImageLayout(handle, layout) == 0);
        CHECK(layout.pixelFormat == format && layout.planes.size() == expected.size());
        // 按公共平面步长访问非正方形图案
        std::vector<uint8_t> pixels(size, 0xa5);
        for (size_t plane = 0; plane < expected.size(); ++plane) {
            const auto &got = layout.planes[plane];
            const auto &want = expected[plane];
            CHECK(got.offset == want.offset && got.hStride == want.rowStride);
            CHECK(got.vStride == want.columnStride);
            for (uint32_t y = 0; y < want.height; ++y) {
                for (uint32_t x = 0; x < want.width; ++x) {
                    const size_t offset = want.offset + y * want.rowStride + x * want.columnStride;
                    CHECK(offset < pixels.size());
                    pixels[offset] = uint8_t(17 * plane + 3 * y + 5 * x);
                }
            }
            for (uint32_t y = 0; y < want.height; ++y) {
                for (uint32_t x = 0; x < want.width; ++x) {
                    const size_t offset = got.offset + y * got.hStride + x * got.vStride;
                    CHECK(offset < pixels.size());
                    CHECK(pixels[offset] == uint8_t(17 * plane + 3 * y + 5 * x));
                }
            }
        }
        std::printf("PLANE_CASE_PASS format=%u width=%u height=%u stride=%u planes=%zu\n",
            format, width, height, stride, layout.planes.size());
        ++cases;
        return 0;
    };
    CHECK(checkLayout(3, 74, 30, 256, 12288, {{0, 256, 2, 74, 30}}) == 0);
    for (uint32_t format : {11u, 12u, 19u, 20u}) {
        CHECK(checkLayout(format, 73, 29, 384, 16384, {{0, 384, 4, 73, 29}}) == 0);
    }
    for (uint32_t format : {24u, 25u}) {
        CHECK(checkLayout(format, 70, 46, 128, 12288,
            {{0, 128, 1, 70, 46}, {5888, 128, 2, 35, 23}}) == 0);
    }
    for (uint32_t format : {28u, 29u}) {
        CHECK(checkLayout(format, 70, 46, 128, 12288,
            {{0, 128, 1, 70, 46}, {5888, 64, 1, 35, 23}, {7360, 64, 1, 35, 23}}) == 0);
    }
    CHECK(checkLayout(38, 37, 1, 37, 4096, {{0, 37, 1, 37, 1}}) == 0);

    BufferHandle valid{};
    valid.fd = 0;
    valid.width = 70;
    valid.height = 46;
    valid.format = 24;
    valid.stride = 128;
    valid.size = 12288;
    valid.usage = 9;
    // 无效布局保留调用方已有输出
    for (unsigned invalid = 0; invalid < 8; ++invalid) {
        BufferHandle handle = valid;
        switch (invalid) {
            case 0: handle.fd = -1; break;
            case 1: handle.width = 0; break;
            case 2: handle.height = 45; break;
            case 3: handle.stride = 127; break;
            case 4: handle.size = 100; break;
            case 5: handle.reserveFds = 1; break;
            case 6: handle.format = 999; break;
            case 7: handle.usage = 1ULL << 63; break;
        }
        V1_2::ImageLayout layout{};
        layout.pixelFormat = 77;
        layout.planes = {{123, 456, 789}};
        CHECK(vdi->GetImageLayout(handle, layout) == -3);
        CHECK(layout.pixelFormat == 77 && layout.planes.size() == 1);
        CHECK(layout.planes[0].offset == 123 && layout.planes[0].hStride == 456 && layout.planes[0].vStride == 789);
        ++cases;
    }
    V1_0::DestroyDisplayBufferVdi(vdi);
    std::printf("PLANE_LAYOUT_CONTRACT=0 cases=%u dma_allocations=0 physical_commits=0\n", cases);
    return 0;
}
