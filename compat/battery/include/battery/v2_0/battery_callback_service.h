/*
 * Copyright (c) 2023 Huawei Device Co., Ltd.
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

#ifndef OHOS_HDI_BATTERY_V2_0_BATTERYCALLBACKSERVICE_H
#define OHOS_HDI_BATTERY_V2_0_BATTERYCALLBACKSERVICE_H

#include "v2_0/ibattery_callback.h"

namespace OHOS {
namespace HDI {
namespace Battery {
namespace V2_0 {
class BatteryCallbackService : public OHOS::HDI::Battery::V2_0::IBatteryCallback {
public:
    BatteryCallbackService() = default;
    virtual ~BatteryCallbackService() = default;

    int32_t Update(const OHOS::HDI::Battery::V2_0::BatteryInfo& event) override;

};
} // V2_0
} // Battery
} // HDI
} // OHOS

#endif // OHOS_HDI_BATTERY_V2_0_BATTERYCALLBACKSERVICE_H