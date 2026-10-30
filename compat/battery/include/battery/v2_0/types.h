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

#ifndef OHOS_HDI_BATTERY_V2_0_TYPES_H
#define OHOS_HDI_BATTERY_V2_0_TYPES_H

#include <cstdbool>
#include <cstdint>
#include <string>

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
class MessageParcel;
}

namespace OHOS {
namespace HDI {
namespace Battery {
namespace V2_0 {

using namespace OHOS;

enum BatteryHealthState : int32_t {
    BATTERY_HEALTH_UNKNOWN = 0,
    BATTERY_HEALTH_GOOD,
    BATTERY_HEALTH_OVERHEAT,
    BATTERY_HEALTH_OVERVOLTAGE,
    BATTERY_HEALTH_COLD,
    BATTERY_HEALTH_DEAD,
    BATTERY_HEALTH_RESERVED,
};

enum BatteryChargeState : int32_t {
    CHARGE_STATE_NONE = 0,
    CHARGE_STATE_ENABLE,
    CHARGE_STATE_DISABLE,
    CHARGE_STATE_FULL,
    CHARGE_STATE_RESERVED,
};

enum BatteryPluggedType : int32_t {
    PLUGGED_TYPE_NONE = 0,
    PLUGGED_TYPE_AC,
    PLUGGED_TYPE_USB,
    PLUGGED_TYPE_WIRELESS,
    PLUGGED_TYPE_BUTT,
};

struct BatteryInfo {
    int32_t capacity;
    int32_t voltage;
    int32_t temperature;
    int32_t healthState;
    int32_t pluggedType;
    int32_t pluggedMaxCurrent;
    int32_t pluggedMaxVoltage;
    int32_t chargeState;
    int32_t chargeCounter;
    int32_t totalEnergy;
    int32_t curAverage;
    int32_t curNow;
    int32_t remainEnergy;
    int8_t present;
    std::string technology;
    std::string uevent;
};

enum ChargingLimitType : int32_t {
    TYPE_CURRENT = 0,
    TYPE_VOLTAGE,
};

struct ChargingLimit {
    OHOS::HDI::Battery::V2_0::ChargingLimitType type;
    std::string protocol;
    int32_t value;
};

enum ChargeType : int32_t {
    CHARGE_TYPE_NONE = 0,
    CHARGE_TYPE_WIRED_NORMAL,
    CHARGE_TYPE_WIRED_QUICK,
    CHARGE_TYPE_WIRED_SUPER_QUICK,
    CHARGE_TYPE_WIRELESS_NORMAL,
    CHARGE_TYPE_WIRELESS_QUICK,
    CHARGE_TYPE_WIRELESS_SUPER_QUICK,
};

bool BatteryInfoBlockMarshalling(OHOS::MessageParcel &data, const OHOS::HDI::Battery::V2_0::BatteryInfo& dataBlock);

bool BatteryInfoBlockUnmarshalling(OHOS::MessageParcel &data, OHOS::HDI::Battery::V2_0::BatteryInfo& dataBlock);

bool ChargingLimitBlockMarshalling(OHOS::MessageParcel &data, const OHOS::HDI::Battery::V2_0::ChargingLimit& dataBlock);

bool ChargingLimitBlockUnmarshalling(OHOS::MessageParcel &data, OHOS::HDI::Battery::V2_0::ChargingLimit& dataBlock);


} // V2_0
} // Battery
} // HDI
} // OHOS

#endif // OHOS_HDI_BATTERY_V2_0_TYPES_H