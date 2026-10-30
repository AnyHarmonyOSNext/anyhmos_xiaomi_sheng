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

#ifndef OHOS_HDI_BATTERY_V2_0_IBATTERYINTERFACE_H
#define OHOS_HDI_BATTERY_V2_0_IBATTERYINTERFACE_H

#include <stdint.h>
#include <string>
#include <vector>
#include <hdf_base.h>
#include <hdi_base.h>
#include "battery/v2_0/ibattery_callback.h"
#include "battery/v2_0/types.h"

#ifndef HDI_BUFF_MAX_SIZE
#define HDI_BUFF_MAX_SIZE (1024 * 200)
#endif

#ifndef HDI_CHECK_VALUE_RETURN
#define HDI_CHECK_VALUE_RETURN(lv, compare, rv, ret) do { \
    if ((lv) compare (rv)) { \
        return ret; \
    } \
} while (false)
#endif

#ifndef HDI_CHECK_VALUE_RET_GOTO
#define HDI_CHECK_VALUE_RET_GOTO(lv, compare, rv, ret, value, table) do { \
    if ((lv) compare (rv)) { \
        ret = value; \
        goto table; \
    } \
} while (false)
#endif

namespace OHOS {
namespace HDI {
namespace Battery {
namespace V2_0 {
using namespace OHOS;
using namespace OHOS::HDI;

enum {
    CMD_BATTERY_INTERFACE_GET_VERSION = 0,
    CMD_BATTERY_INTERFACE_REGISTER = 1,
    CMD_BATTERY_INTERFACE_UN_REGISTER = 2,
    CMD_BATTERY_INTERFACE_CHANGE_PATH = 3,
    CMD_BATTERY_INTERFACE_GET_CAPACITY = 4,
    CMD_BATTERY_INTERFACE_GET_VOLTAGE = 5,
    CMD_BATTERY_INTERFACE_GET_TEMPERATURE = 6,
    CMD_BATTERY_INTERFACE_GET_HEALTH_STATE = 7,
    CMD_BATTERY_INTERFACE_GET_PLUGGED_TYPE = 8,
    CMD_BATTERY_INTERFACE_GET_CHARGE_STATE = 9,
    CMD_BATTERY_INTERFACE_GET_PRESENT = 10,
    CMD_BATTERY_INTERFACE_GET_TECHNOLOGY = 11,
    CMD_BATTERY_INTERFACE_GET_TOTAL_ENERGY = 12,
    CMD_BATTERY_INTERFACE_GET_CURRENT_AVERAGE = 13,
    CMD_BATTERY_INTERFACE_GET_CURRENT_NOW = 14,
    CMD_BATTERY_INTERFACE_GET_REMAIN_ENERGY = 15,
    CMD_BATTERY_INTERFACE_GET_BATTERY_INFO = 16,
    CMD_BATTERY_INTERFACE_SET_CHARGING_LIMIT = 17,
    CMD_BATTERY_INTERFACE_GET_CHARGE_TYPE = 18,
    CMD_BATTERY_INTERFACE_SET_BATTERY_CONFIG = 19,
    CMD_BATTERY_INTERFACE_GET_BATTERY_CONFIG = 20,
    CMD_BATTERY_INTERFACE_IS_BATTERY_CONFIG_SUPPORTED = 21,
};

class IBatteryInterface : public HdiBase {
public:
    DECLARE_HDI_DESCRIPTOR(u"ohos.hdi.battery.v2_0.IBatteryInterface");

    virtual ~IBatteryInterface() = default;

    static sptr<OHOS::HDI::Battery::V2_0::IBatteryInterface> Get(bool isStub = false);
    static sptr<OHOS::HDI::Battery::V2_0::IBatteryInterface> Get(const std::string &serviceName, bool isStub = false);

    virtual int32_t Register(const sptr<OHOS::HDI::Battery::V2_0::IBatteryCallback>& event) = 0;

    virtual int32_t UnRegister() = 0;

    virtual int32_t ChangePath(const std::string& path) = 0;

    virtual int32_t GetCapacity(int32_t& capacity) = 0;

    virtual int32_t GetVoltage(int32_t& voltage) = 0;

    virtual int32_t GetTemperature(int32_t& temperature) = 0;

    virtual int32_t GetHealthState(OHOS::HDI::Battery::V2_0::BatteryHealthState& healthState) = 0;

    virtual int32_t GetPluggedType(OHOS::HDI::Battery::V2_0::BatteryPluggedType& pluggedType) = 0;

    virtual int32_t GetChargeState(OHOS::HDI::Battery::V2_0::BatteryChargeState& chargeState) = 0;

    virtual int32_t GetPresent(bool& present) = 0;

    virtual int32_t GetTechnology(std::string& technology) = 0;

    virtual int32_t GetTotalEnergy(int32_t& totalEnergy) = 0;

    virtual int32_t GetCurrentAverage(int32_t& curAverage) = 0;

    virtual int32_t GetCurrentNow(int32_t& curNow) = 0;

    virtual int32_t GetRemainEnergy(int32_t& remainEnergy) = 0;

    virtual int32_t GetBatteryInfo(OHOS::HDI::Battery::V2_0::BatteryInfo& info) = 0;

    virtual int32_t SetChargingLimit(const std::vector<OHOS::HDI::Battery::V2_0::ChargingLimit>& chargingLimit) = 0;

    virtual int32_t GetChargeType(OHOS::HDI::Battery::V2_0::ChargeType& type) = 0;

    virtual int32_t SetBatteryConfig(const std::string& sceneName, const std::string& value) = 0;

    virtual int32_t GetBatteryConfig(const std::string& sceneName, std::string& value) = 0;

    virtual int32_t IsBatteryConfigSupported(const std::string& sceneName, bool& value) = 0;

    virtual int32_t GetVersion(uint32_t& majorVer, uint32_t& minorVer)
    {
        majorVer = 2;
        minorVer = 0;
        return HDF_SUCCESS;
    }

    virtual bool IsProxy()
    {
        return false;
    }

    virtual const std::u16string GetDesc()
    {
        return metaDescriptor_;
    }
};
} // V2_0
} // Battery
} // HDI
} // OHOS

#endif // OHOS_HDI_BATTERY_V2_0_IBATTERYINTERFACE_H