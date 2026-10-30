/*
 * Copyright (c) 2025 Huawei Device Co., Ltd.
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

#ifndef OHOS_HDI_USER_AUTH_V4_0_MESSAGECALLBACKPROXY_H
#define OHOS_HDI_USER_AUTH_V4_0_MESSAGECALLBACKPROXY_H

#include "v4_0/imessage_callback.h"
#include <iproxy_broker.h>

namespace OHOS {
namespace HDI {
namespace UserAuth {
namespace V4_0 {

class MessageCallbackProxy : public IProxyBroker<OHOS::HDI::UserAuth::V4_0::IMessageCallback> {
public:
    explicit MessageCallbackProxy(const sptr<IRemoteObject>& remote) : IProxyBroker<OHOS::HDI::UserAuth::V4_0::IMessageCallback>(remote) {
    }
    virtual ~MessageCallbackProxy() = default;

    inline bool IsProxy() override
    {
        return true;
    }

    int32_t OnMessage(uint64_t scheduleId, int32_t destRole, const std::vector<uint8_t>& msg) override;

    int32_t GetVersion(uint32_t& majorVer, uint32_t& minorVer) override;

    static int32_t OnMessage_(uint64_t scheduleId, int32_t destRole, const std::vector<uint8_t>& msg,
         const sptr<IRemoteObject> remote);

    static int32_t GetVersion_(uint32_t& majorVer, uint32_t& minorVer, const sptr<IRemoteObject> remote);

private:
    static inline BrokerDelegator<OHOS::HDI::UserAuth::V4_0::MessageCallbackProxy> delegator_;
};

} // V4_0
} // UserAuth
} // HDI
} // OHOS

#endif // OHOS_HDI_USER_AUTH_V4_0_MESSAGECALLBACKPROXY_H