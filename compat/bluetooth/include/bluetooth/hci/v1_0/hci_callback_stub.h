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

#ifndef OHOS_HDI_BLUETOOTH_HCI_V1_0_HCICALLBACKSTUB_H
#define OHOS_HDI_BLUETOOTH_HCI_V1_0_HCICALLBACKSTUB_H

#include <ipc_object_stub.h>
#include <message_option.h>
#include <message_parcel.h>
#include <object_collector.h>
#include <refbase.h>
#include "v1_0/ihci_callback.h"

namespace OHOS {
namespace HDI {
namespace Bluetooth {
namespace Hci {
namespace V1_0 {

using namespace OHOS;
class HciCallbackStub : public IPCObjectStub {
public:
    explicit HciCallbackStub(const sptr<IHciCallback> &impl);
    virtual ~HciCallbackStub();

    int32_t OnRemoteRequest(uint32_t code, MessageParcel &data, MessageParcel &reply, MessageOption &option) override;

    static int32_t HciCallbackStubOnInited_(MessageParcel& hciCallbackData, MessageParcel& hciCallbackReply, MessageOption& hciCallbackOption, sptr<OHOS::HDI::Bluetooth::Hci::V1_0::IHciCallback> impl);

    static int32_t HciCallbackStubOnReceivedHciPacket_(MessageParcel& hciCallbackData, MessageParcel& hciCallbackReply, MessageOption& hciCallbackOption, sptr<OHOS::HDI::Bluetooth::Hci::V1_0::IHciCallback> impl);

    static int32_t HciCallbackStubGetVersion_(MessageParcel& hciCallbackData, MessageParcel& hciCallbackReply, MessageOption& hciCallbackOption, sptr<OHOS::HDI::Bluetooth::Hci::V1_0::IHciCallback> impl);

private:
    int32_t HciCallbackStubOnInited(MessageParcel& hciCallbackData, MessageParcel& hciCallbackReply, MessageOption& hciCallbackOption);

    int32_t HciCallbackStubOnReceivedHciPacket(MessageParcel& hciCallbackData, MessageParcel& hciCallbackReply, MessageOption& hciCallbackOption);

    int32_t HciCallbackStubGetVersion(MessageParcel& hciCallbackData, MessageParcel& hciCallbackReply, MessageOption& hciCallbackOption);


    static inline ObjectDelegator<OHOS::HDI::Bluetooth::Hci::V1_0::HciCallbackStub, OHOS::HDI::Bluetooth::Hci::V1_0::IHciCallback> objDelegator_;
    sptr<OHOS::HDI::Bluetooth::Hci::V1_0::IHciCallback> impl_;
};
} // V1_0
} // Hci
} // Bluetooth
} // HDI
} // OHOS

#endif // OHOS_HDI_BLUETOOTH_HCI_V1_0_HCICALLBACKSTUB_H