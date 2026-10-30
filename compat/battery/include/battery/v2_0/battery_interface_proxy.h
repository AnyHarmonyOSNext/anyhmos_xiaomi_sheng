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

#ifndef OHOS_HDI_BATTERY_V2_0_BATTERYINTERFACEPROXY_H
#define OHOS_HDI_BATTERY_V2_0_BATTERYINTERFACEPROXY_H

#include "v2_0/ibattery_interface.h"
#include <unistd.h>
#include <iproxy_broker.h>

namespace OHOS {
namespace HDI {
namespace Battery {
namespace V2_0 {

class BatteryInterfaceProxy : public IProxyBroker<OHOS::HDI::Battery::V2_0::IBatteryInterface> {
public:
    class IServiceManagerDeathRecipient : public IRemoteObject::DeathRecipient {
    public:
        IServiceManagerDeathRecipient(wptr<OHOS::HDI::Battery::V2_0::BatteryInterfaceProxy> proxy) : proxy_(proxy) {} 
        ~IServiceManagerDeathRecipient() override = default;
        void OnRemoteDied(const wptr<IRemoteObject> &remote) override
        {
            int32_t result = HDF_FAILURE;
            const int sleepInterval = 500000;
            const int waitTimes = 10;
            int currentTime = waitTimes;
            do {
                usleep(sleepInterval);
                auto proxy = proxy_.promote();
                if (proxy != nullptr) {
                    result = OHOS::HDI::Battery::V2_0::BatteryInterfaceProxy::Reconnect(proxy);
                }
                --currentTime;
            } while (result != HDF_SUCCESS && currentTime >0);
        }
    private:
        wptr<OHOS::HDI::Battery::V2_0::BatteryInterfaceProxy> proxy_;
    };

    explicit BatteryInterfaceProxy(const sptr<IRemoteObject>& remote) : IProxyBroker<OHOS::HDI::Battery::V2_0::IBatteryInterface>(remote) {
        reconnectRemote_ = nullptr;
        servMgr_ = nullptr;
        deathRecipient_ = nullptr;
        isReconnected_ = false;
    }
    virtual ~BatteryInterfaceProxy() {
        if (servMgr_ != nullptr && deathRecipient_ != nullptr) {
            servMgr_->RemoveDeathRecipient(deathRecipient_);
        }
    }

    inline bool IsProxy() override
    {
        return true;
    }

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

    int32_t GetVersion(uint32_t& majorVer, uint32_t& minorVer) override;

    static int32_t Register_(const sptr<OHOS::HDI::Battery::V2_0::IBatteryCallback>& event,
         const sptr<IRemoteObject> remote);

    static int32_t UnRegister_(const sptr<IRemoteObject> remote);

    static int32_t ChangePath_(const std::string& path, const sptr<IRemoteObject> remote);

    static int32_t GetCapacity_(int32_t& capacity, const sptr<IRemoteObject> remote);

    static int32_t GetVoltage_(int32_t& voltage, const sptr<IRemoteObject> remote);

    static int32_t GetTemperature_(int32_t& temperature, const sptr<IRemoteObject> remote);

    static int32_t GetHealthState_(OHOS::HDI::Battery::V2_0::BatteryHealthState& healthState,
         const sptr<IRemoteObject> remote);

    static int32_t GetPluggedType_(OHOS::HDI::Battery::V2_0::BatteryPluggedType& pluggedType,
         const sptr<IRemoteObject> remote);

    static int32_t GetChargeState_(OHOS::HDI::Battery::V2_0::BatteryChargeState& chargeState,
         const sptr<IRemoteObject> remote);

    static int32_t GetPresent_(bool& present, const sptr<IRemoteObject> remote);

    static int32_t GetTechnology_(std::string& technology, const sptr<IRemoteObject> remote);

    static int32_t GetTotalEnergy_(int32_t& totalEnergy, const sptr<IRemoteObject> remote);

    static int32_t GetCurrentAverage_(int32_t& curAverage, const sptr<IRemoteObject> remote);

    static int32_t GetCurrentNow_(int32_t& curNow, const sptr<IRemoteObject> remote);

    static int32_t GetRemainEnergy_(int32_t& remainEnergy, const sptr<IRemoteObject> remote);

    static int32_t GetBatteryInfo_(OHOS::HDI::Battery::V2_0::BatteryInfo& info, const sptr<IRemoteObject> remote);

    static int32_t SetChargingLimit_(const std::vector<OHOS::HDI::Battery::V2_0::ChargingLimit>& chargingLimit,
         const sptr<IRemoteObject> remote);

    static int32_t GetChargeType_(OHOS::HDI::Battery::V2_0::ChargeType& type, const sptr<IRemoteObject> remote);

    static int32_t SetBatteryConfig_(const std::string& sceneName, const std::string& value,
         const sptr<IRemoteObject> remote);

    static int32_t GetBatteryConfig_(const std::string& sceneName, std::string& value,
         const sptr<IRemoteObject> remote);

    static int32_t IsBatteryConfigSupported_(const std::string& sceneName, bool& value,
         const sptr<IRemoteObject> remote);

    static int32_t GetVersion_(uint32_t& majorVer, uint32_t& minorVer, const sptr<IRemoteObject> remote);

    static int32_t Reconnect(sptr<OHOS::HDI::Battery::V2_0::BatteryInterfaceProxy> proxy);

    sptr<IRemoteObject> GetCurrentRemote() {
        return isReconnected_ ? reconnectRemote_ : Remote();
    }

    bool isReconnected_;
    std::string serviceName_;
    sptr<IRemoteObject> servMgr_;
    sptr<OHOS::HDI::Battery::V2_0::BatteryInterfaceProxy::IServiceManagerDeathRecipient> deathRecipient_;
    sptr<IRemoteObject> reconnectRemote_;
private:
    static inline BrokerDelegator<OHOS::HDI::Battery::V2_0::BatteryInterfaceProxy> delegator_;
};

} // V2_0
} // Battery
} // HDI
} // OHOS

#endif // OHOS_HDI_BATTERY_V2_0_BATTERYINTERFACEPROXY_H