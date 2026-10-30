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

#ifndef OHOS_HDI_BATTERY_V2_0_BATTERYINTERFACESERVICE_H
#define OHOS_HDI_BATTERY_V2_0_BATTERYINTERFACESERVICE_H

#include "v2_0/ibattery_interface.h"

namespace OHOS {
namespace HDI {
namespace Battery {
namespace V2_0 {
class BatteryInterfaceService : public OHOS::HDI::Battery::V2_0::IBatteryInterface {
public:
    BatteryInterfaceService() = default;
    virtual ~BatteryInterfaceService() = default;

    int32_t Register(const sptr<OHOS::HDI::Battery::V2_0::IBatteryCallback>& event) override;

    int32_t UnRegister() override;

    int32_t ChangePath(const std::string& path) override;

    int32_t GetCapacity(int32_t& capacity) override;

    int32_t GetVoltage(int32_t& voltage) override;

    int32_t GetTemperature(int32_t& temperature) override;

    int32_t GetHealthState(OHOS::HDI::Battery::V2_0::BatteryHealthState& healthState) override;

    int32_t GetPluggedType(OHOS::HDI::Battery::V2_0::BatteryPluggedType& pluggedType) override;

    int32_t GetChargeState(OHOS::HDI::Battery::V2_0::BatteryChargeState& chargeState) override;

    int32_t GetPresent(bool& present) override;

    int32_t GetTechnology(std::string& technology) override;

    int32_t GetTotalEnergy(int32_t& totalEnergy) override;

    int32_t GetCurrentAverage(int32_t& curAverage) override;

    int32_t GetCurrentNow(int32_t& curNow) override;

    int32_t GetRemainEnergy(int32_t& remainEnergy) override;

    int32_t GetBatteryInfo(OHOS::HDI::Battery::V2_0::BatteryInfo& info) override;

    int32_t SetChargingLimit(const std::vector<OHOS::HDI::Battery::V2_0::ChargingLimit>& chargingLimit) override;

    int32_t GetChargeType(OHOS::HDI::Battery::V2_0::ChargeType& type) override;

    int32_t SetBatteryConfig(const std::string& sceneName, const std::string& value) override;

    int32_t GetBatteryConfig(const std::string& sceneName, std::string& value) override;

    int32_t IsBatteryConfigSupported(const std::string& sceneName, bool& value) override;

};
} // V2_0
} // Battery
} // HDI
} // OHOS

#endif // OHOS_HDI_BATTERY_V2_0_BATTERYINTERFACESERVICE_H