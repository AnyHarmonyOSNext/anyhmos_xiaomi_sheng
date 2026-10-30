/*
 * Copyright (c) 2022 Huawei Device Co., Ltd.
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

#ifndef OHOS_HDI_BLUETOOTH_HCI_V1_0_HCIINTERFACEPROXY_H
#define OHOS_HDI_BLUETOOTH_HCI_V1_0_HCIINTERFACEPROXY_H

#include "v1_0/ihci_interface.h"
#include <unistd.h>
#include <iproxy_broker.h>

namespace OHOS {
namespace HDI {
namespace Bluetooth {
namespace Hci {
namespace V1_0 {

class HciInterfaceProxy : public IProxyBroker<OHOS::HDI::Bluetooth::Hci::V1_0::IHciInterface> {
public:
    class IServiceManagerDeathRecipient : public IRemoteObject::DeathRecipient {
    public:
        IServiceManagerDeathRecipient(wptr<OHOS::HDI::Bluetooth::Hci::V1_0::HciInterfaceProxy> proxy) : proxy_(proxy) {} 
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
                    result = OHOS::HDI::Bluetooth::Hci::V1_0::HciInterfaceProxy::Reconnect(proxy);
                }
                --currentTime;
            } while (result != HDF_SUCCESS && currentTime >0);
        }
    private:
        wptr<OHOS::HDI::Bluetooth::Hci::V1_0::HciInterfaceProxy> proxy_;
    };

    explicit HciInterfaceProxy(const sptr<IRemoteObject>& remote) : IProxyBroker<OHOS::HDI::Bluetooth::Hci::V1_0::IHciInterface>(remote) {
        reconnectRemote_ = nullptr;
        servMgr_ = nullptr;
        deathRecipient_ = nullptr;
        isReconnected_ = false;
    }
    virtual ~HciInterfaceProxy() {
        if (servMgr_ != nullptr && deathRecipient_ != nullptr) {
            servMgr_->RemoveDeathRecipient(deathRecipient_);
        }
    }

    inline bool IsProxy() override
    {
        return true;
    }

    int32_t Init(const sptr<OHOS::HDI::Bluetooth::Hci::V1_0::IHciCallback>& callbackObj) override;

    int32_t SendHciPacket(OHOS::HDI::Bluetooth::Hci::V1_0::BtType type, const std::vector<uint8_t>& data) override;

    int32_t Close() override;

    int32_t GetVersion(uint32_t& majorVer, uint32_t& minorVer) override;

    static int32_t Init_(const sptr<OHOS::HDI::Bluetooth::Hci::V1_0::IHciCallback>& callbackObj,
         const sptr<IRemoteObject> remote);

    static int32_t SendHciPacket_(OHOS::HDI::Bluetooth::Hci::V1_0::BtType type, const std::vector<uint8_t>& data,
         const sptr<IRemoteObject> remote);

    static int32_t Close_(const sptr<IRemoteObject> remote);

    static int32_t GetVersion_(uint32_t& majorVer, uint32_t& minorVer, const sptr<IRemoteObject> remote);

    static int32_t Reconnect(sptr<OHOS::HDI::Bluetooth::Hci::V1_0::HciInterfaceProxy> proxy);

    sptr<IRemoteObject> GetCurrentRemote() {
        return isReconnected_ ? reconnectRemote_ : Remote();
    }

    bool isReconnected_;
    std::string serviceName_;
    sptr<IRemoteObject> servMgr_;
    sptr<OHOS::HDI::Bluetooth::Hci::V1_0::HciInterfaceProxy::IServiceManagerDeathRecipient> deathRecipient_;
    sptr<IRemoteObject> reconnectRemote_;
private:
    static inline BrokerDelegator<OHOS::HDI::Bluetooth::Hci::V1_0::HciInterfaceProxy> delegator_;
};

} // V1_0
} // Hci
} // Bluetooth
} // HDI
} // OHOS

#endif // OHOS_HDI_BLUETOOTH_HCI_V1_0_HCIINTERFACEPROXY_H