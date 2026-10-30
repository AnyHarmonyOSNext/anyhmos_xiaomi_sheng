/*
 * Copyright (c) 2024 Huawei Device Co., Ltd.
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 *     http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 */

#ifndef OHOS_HDI_DISPLAY_BUFFER_V1_2_DISPLAYBUFFERTYPE_H
#define OHOS_HDI_DISPLAY_BUFFER_V1_2_DISPLAYBUFFERTYPE_H

#include <cstdbool>
#include <cstdint>
#include <vector>
#include "display/buffer/v1_0/display_buffer_type.h"

namespace OHOS {
namespace HDI {
namespace Display {
namespace Buffer {
namespace V1_2 {

using namespace OHOS;
using namespace OHOS::HDI::Display::Buffer::V1_0;

struct ImagePlane {
    uint32_t offset;
    uint32_t hStride;
    uint32_t vStride;
} __attribute__ ((aligned(8)));

struct ImageLayout {
    uint32_t pixelFormat;
    std::vector<OHOS::HDI::Display::Buffer::V1_2::ImagePlane> planes;
};
} // V1_2
} // Buffer
} // Display
} // HDI
} // OHOS

#endif // OHOS_HDI_DISPLAY_BUFFER_V1_2_DISPLAYBUFFERTYPE_H