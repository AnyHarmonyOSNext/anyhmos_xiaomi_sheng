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

#ifndef OHOS_HDI_BATTERY_V2_0_BATTERYINTERFACESTUB_H
#define OHOS_HDI_BATTERY_V2_0_BATTERYINTERFACESTUB_H

#include <ipc_object_stub.h>
#include <message_option.h>
#include <message_parcel.h>
#include <object_collector.h>
#include <refbase.h>
#include "v2_0/ibattery_interface.h"

namespace OHOS {
namespace HDI {
namespace Battery {
namespace V2_0 {

using namespace OHOS;
class BatteryInterfaceStub : public IPCObjectStub {
public:
    explicit BatteryInterfaceStub(const sptr<IBatteryInterface> &impl);
    virtual ~BatteryInterfaceStub();

    int32_t OnRemoteRequest(uint32_t code, MessageParcel &data, MessageParcel &reply, MessageOption &option) override;

    static int32_t BatteryInterfaceStubRegister_(MessageParcel& batteryInterfaceData, MessageParcel& batteryInterfaceReply, MessageOption& batteryInterfaceOption, sptr<OHOS::HDI::Battery::V2_0::IBatteryInterface> impl);

    static int32_t BatteryInterfaceStubUnRegister_(MessageParcel& batteryInterfaceData, MessageParcel& batteryInterfaceReply, MessageOption& batteryInterfaceOption, sptr<OHOS::HDI::Battery::V2_0::IBatteryInterface> impl);

    static int32_t BatteryInterfaceStubChangePath_(MessageParcel& batteryInterfaceData, MessageParcel& batteryInterfaceReply, MessageOption& batteryInterfaceOption, sptr<OHOS::HDI::Battery::V2_0::IBatteryInterface> impl);

    static int32_t BatteryInterfaceStubGetCapacity_(MessageParcel& batteryInterfaceData, MessageParcel& batteryInterfaceReply, MessageOption& batteryInterfaceOption, sptr<OHOS::HDI::Battery::V2_0::IBatteryInterface> impl);

    static int32_t BatteryInterfaceStubGetVoltage_(MessageParcel& batteryInterfaceData, MessageParcel& batteryInterfaceReply, MessageOption& batteryInterfaceOption, sptr<OHOS::HDI::Battery::V2_0::IBatteryInterface> impl);

    static int32_t BatteryInterfaceStubGetTemperature_(MessageParcel& batteryInterfaceData, MessageParcel& batteryInterfaceReply, MessageOption& batteryInterfaceOption, sptr<OHOS::HDI::Battery::V2_0::IBatteryInterface> impl);

    static int32_t BatteryInterfaceStubGetHealthState_(MessageParcel& batteryInterfaceData, MessageParcel& batteryInterfaceReply, MessageOption& batteryInterfaceOption, sptr<OHOS::HDI::Battery::V2_0::IBatteryInterface> impl);

    static int32_t BatteryInterfaceStubGetPluggedType_(MessageParcel& batteryInterfaceData, MessageParcel& batteryInterfaceReply, MessageOption& batteryInterfaceOption, sptr<OHOS::HDI::Battery::V2_0::IBatteryInterface> impl);

    static int32_t BatteryInterfaceStubGetChargeState_(MessageParcel& batteryInterfaceData, MessageParcel& batteryInterfaceReply, MessageOption& batteryInterfaceOption, sptr<OHOS::HDI::Battery::V2_0::IBatteryInterface> impl);

    static int32_t BatteryInterfaceStubGetPresent_(MessageParcel& batteryInterfaceData, MessageParcel& batteryInterfaceReply, MessageOption& batteryInterfaceOption, sptr<OHOS::HDI::Battery::V2_0::IBatteryInterface> impl);

    static int32_t BatteryInterfaceStubGetTechnology_(MessageParcel& batteryInterfaceData, MessageParcel& batteryInterfaceReply, MessageOption& batteryInterfaceOption, sptr<OHOS::HDI::Battery::V2_0::IBatteryInterface> impl);

    static int32_t BatteryInterfaceStubGetTotalEnergy_(MessageParcel& batteryInterfaceData, MessageParcel& batteryInterfaceReply, MessageOption& batteryInterfaceOption, sptr<OHOS::HDI::Battery::V2_0::IBatteryInterface> impl);

    static int32_t BatteryInterfaceStubGetCurrentAverage_(MessageParcel& batteryInterfaceData, MessageParcel& batteryInterfaceReply, MessageOption& batteryInterfaceOption, sptr<OHOS::HDI::Battery::V2_0::IBatteryInterface> impl);

    static int32_t BatteryInterfaceStubGetCurrentNow_(MessageParcel& batteryInterfaceData, MessageParcel& batteryInterfaceReply, MessageOption& batteryInterfaceOption, sptr<OHOS::HDI::Battery::V2_0::IBatteryInterface> impl);

    static int32_t BatteryInterfaceStubGetRemainEnergy_(MessageParcel& batteryInterfaceData, MessageParcel& batteryInterfaceReply, MessageOption& batteryInterfaceOption, sptr<OHOS::HDI::Battery::V2_0::IBatteryInterface> impl);

    static int32_t BatteryInterfaceStubGetBatteryInfo_(MessageParcel& batteryInterfaceData, MessageParcel& batteryInterfaceReply, MessageOption& batteryInterfaceOption, sptr<OHOS::HDI::Battery::V2_0::IBatteryInterface> impl);

    static int32_t BatteryInterfaceStubSetChargingLimit_(MessageParcel& batteryInterfaceData, MessageParcel& batteryInterfaceReply, MessageOption& batteryInterfaceOption, sptr<OHOS::HDI::Battery::V2_0::IBatteryInterface> impl);

    static int32_t BatteryInterfaceStubGetChargeType_(MessageParcel& batteryInterfaceData, MessageParcel& batteryInterfaceReply, MessageOption& batteryInterfaceOption, sptr<OHOS::HDI::Battery::V2_0::IBatteryInterface> impl);

    static int32_t BatteryInterfaceStubSetBatteryConfig_(MessageParcel& batteryInterfaceData, MessageParcel& batteryInterfaceReply, MessageOption& batteryInterfaceOption, sptr<OHOS::HDI::Battery::V2_0::IBatteryInterface> impl);

    static int32_t BatteryInterfaceStubGetBatteryConfig_(MessageParcel& batteryInterfaceData, MessageParcel& batteryInterfaceReply, MessageOption& batteryInterfaceOption, sptr<OHOS::HDI::Battery::V2_0::IBatteryInterface> impl);

    static int32_t BatteryInterfaceStubIsBatteryConfigSupported_(MessageParcel& batteryInterfaceData, MessageParcel& batteryInterfaceReply, MessageOption& batteryInterfaceOption, sptr<OHOS::HDI::Battery::V2_0::IBatteryInterface> impl);

    static int32_t BatteryInterfaceStubGetVersion_(MessageParcel& batteryInterfaceData, MessageParcel& batteryInterfaceReply, MessageOption& batteryInterfaceOption, sptr<OHOS::HDI::Battery::V2_0::IBatteryInterface> impl);

private:
    int32_t BatteryInterfaceStubRegister(MessageParcel& batteryInterfaceData, MessageParcel& batteryInterfaceReply, MessageOption& batteryInterfaceOption);

    int32_t BatteryInterfaceStubUnRegister(MessageParcel& batteryInterfaceData, MessageParcel& batteryInterfaceReply, MessageOption& batteryInterfaceOption);

    int32_t BatteryInterfaceStubChangePath(MessageParcel& batteryInterfaceData, MessageParcel& batteryInterfaceReply, MessageOption& batteryInterfaceOption);

    int32_t BatteryInterfaceStubGetCapacity(MessageParcel& batteryInterfaceData, MessageParcel& batteryInterfaceReply, MessageOption& batteryInterfaceOption);

    int32_t BatteryInterfaceStubGetVoltage(MessageParcel& batteryInterfaceData, MessageParcel& batteryInterfaceReply, MessageOption& batteryInterfaceOption);

    int32_t BatteryInterfaceStubGetTemperature(MessageParcel& batteryInterfaceData, MessageParcel& batteryInterfaceReply, MessageOption& batteryInterfaceOption);

    int32_t BatteryInterfaceStubGetHealthState(MessageParcel& batteryInterfaceData, MessageParcel& batteryInterfaceReply, MessageOption& batteryInterfaceOption);

    int32_t BatteryInterfaceStubGetPluggedType(MessageParcel& batteryInterfaceData, MessageParcel& batteryInterfaceReply, MessageOption& batteryInterfaceOption);

    int32_t BatteryInterfaceStubGetChargeState(MessageParcel& batteryInterfaceData, MessageParcel& batteryInterfaceReply, MessageOption& batteryInterfaceOption);

    int32_t BatteryInterfaceStubGetPresent(MessageParcel& batteryInterfaceData, MessageParcel& batteryInterfaceReply, MessageOption& batteryInterfaceOption);

    int32_t BatteryInterfaceStubGetTechnology(MessageParcel& batteryInterfaceData, MessageParcel& batteryInterfaceReply, MessageOption& batteryInterfaceOption);

    int32_t BatteryInterfaceStubGetTotalEnergy(MessageParcel& batteryInterfaceData, MessageParcel& batteryInterfaceReply, MessageOption& batteryInterfaceOption);

    int32_t BatteryInterfaceStubGetCurrentAverage(MessageParcel& batteryInterfaceData, MessageParcel& batteryInterfaceReply, MessageOption& batteryInterfaceOption);

    int32_t BatteryInterfaceStubGetCurrentNow(MessageParcel& batteryInterfaceData, MessageParcel& batteryInterfaceReply, MessageOption& batteryInterfaceOption);

    int32_t BatteryInterfaceStubGetRemainEnergy(MessageParcel& batteryInterfaceData, MessageParcel& batteryInterfaceReply, MessageOption& batteryInterfaceOption);

    int32_t BatteryInterfaceStubGetBatteryInfo(MessageParcel& batteryInterfaceData, MessageParcel& batteryInterfaceReply, MessageOption& batteryInterfaceOption);

    int32_t BatteryInterfaceStubSetChargingLimit(MessageParcel& batteryInterfaceData, MessageParcel& batteryInterfaceReply, MessageOption& batteryInterfaceOption);

    int32_t BatteryInterfaceStubGetChargeType(MessageParcel& batteryInterfaceData, MessageParcel& batteryInterfaceReply, MessageOption& batteryInterfaceOption);

    int32_t BatteryInterfaceStubSetBatteryConfig(MessageParcel& batteryInterfaceData, MessageParcel& batteryInterfaceReply, MessageOption& batteryInterfaceOption);

    int32_t BatteryInterfaceStubGetBatteryConfig(MessageParcel& batteryInterfaceData, MessageParcel& batteryInterfaceReply, MessageOption& batteryInterfaceOption);

    int32_t BatteryInterfaceStubIsBatteryConfigSupported(MessageParcel& batteryInterfaceData, MessageParcel& batteryInterfaceReply, MessageOption& batteryInterfaceOption);

    int32_t BatteryInterfaceStubGetVersion(MessageParcel& batteryInterfaceData, MessageParcel& batteryInterfaceReply, MessageOption& batteryInterfaceOption);


    static inline ObjectDelegator<OHOS::HDI::Battery::V2_0::BatteryInterfaceStub, OHOS::HDI::Battery::V2_0::IBatteryInterface> objDelegator_;
    sptr<OHOS::HDI::Battery::V2_0::IBatteryInterface> impl_;
};
} // V2_0
} // Battery
} // HDI
} // OHOS

#endif // OHOS_HDI_BATTERY_V2_0_BATTERYINTERFACESTUB_H