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

#ifndef OHOS_HDI_USER_AUTH_V4_0_MESSAGECALLBACKSTUB_H
#define OHOS_HDI_USER_AUTH_V4_0_MESSAGECALLBACKSTUB_H

#include <ipc_object_stub.h>
#include <message_option.h>
#include <message_parcel.h>
#include <object_collector.h>
#include <refbase.h>
#include "v4_0/imessage_callback.h"

namespace OHOS {
namespace HDI {
namespace UserAuth {
namespace V4_0 {

using namespace OHOS;
class MessageCallbackStub : public IPCObjectStub {
public:
    explicit MessageCallbackStub(const sptr<IMessageCallback> &impl);
    virtual ~MessageCallbackStub();

    int32_t OnRemoteRequest(uint32_t code, MessageParcel &data, MessageParcel &reply, MessageOption &option) override;

    static int32_t MessageCallbackStubOnMessage_(MessageParcel& messageCallbackData, MessageParcel& messageCallbackReply, MessageOption& messageCallbackOption, sptr<OHOS::HDI::UserAuth::V4_0::IMessageCallback> impl);

    static int32_t MessageCallbackStubGetVersion_(MessageParcel& messageCallbackData, MessageParcel& messageCallbackReply, MessageOption& messageCallbackOption, sptr<OHOS::HDI::UserAuth::V4_0::IMessageCallback> impl);

private:
    int32_t MessageCallbackStubOnMessage(MessageParcel& messageCallbackData, MessageParcel& messageCallbackReply, MessageOption& messageCallbackOption);

    int32_t MessageCallbackStubGetVersion(MessageParcel& messageCallbackData, MessageParcel& messageCallbackReply, MessageOption& messageCallbackOption);


    static inline ObjectDelegator<OHOS::HDI::UserAuth::V4_0::MessageCallbackStub, OHOS::HDI::UserAuth::V4_0::IMessageCallback> objDelegator_;
    sptr<OHOS::HDI::UserAuth::V4_0::IMessageCallback> impl_;
};
} // V4_0
} // UserAuth
} // HDI
} // OHOS

#endif // OHOS_HDI_USER_AUTH_V4_0_MESSAGECALLBACKSTUB_H