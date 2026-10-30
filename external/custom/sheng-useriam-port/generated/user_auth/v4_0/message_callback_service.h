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

#ifndef OHOS_HDI_USER_AUTH_V4_0_MESSAGECALLBACKSERVICE_H
#define OHOS_HDI_USER_AUTH_V4_0_MESSAGECALLBACKSERVICE_H

#include "v4_0/imessage_callback.h"

namespace OHOS {
namespace HDI {
namespace UserAuth {
namespace V4_0 {
class MessageCallbackService : public OHOS::HDI::UserAuth::V4_0::IMessageCallback {
public:
    MessageCallbackService() = default;
    virtual ~MessageCallbackService() = default;

    int32_t OnMessage(uint64_t scheduleId, int32_t destRole, const std::vector<uint8_t>& msg) override;

};
} // V4_0
} // UserAuth
} // HDI
} // OHOS

#endif // OHOS_HDI_USER_AUTH_V4_0_MESSAGECALLBACKSERVICE_H