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

#ifndef OHOS_HDI_BLUETOOTH_HCI_V1_0_HCIINTERFACESTUB_H
#define OHOS_HDI_BLUETOOTH_HCI_V1_0_HCIINTERFACESTUB_H

#include <ipc_object_stub.h>
#include <message_option.h>
#include <message_parcel.h>
#include <object_collector.h>
#include <refbase.h>
#include "v1_0/ihci_interface.h"

namespace OHOS {
namespace HDI {
namespace Bluetooth {
namespace Hci {
namespace V1_0 {

using namespace OHOS;
class HciInterfaceStub : public IPCObjectStub {
public:
    explicit HciInterfaceStub(const sptr<IHciInterface> &impl);
    virtual ~HciInterfaceStub();

    int32_t OnRemoteRequest(uint32_t code, MessageParcel &data, MessageParcel &reply, MessageOption &option) override;

    static int32_t HciInterfaceStubInit_(MessageParcel& hciInterfaceData, MessageParcel& hciInterfaceReply, MessageOption& hciInterfaceOption, sptr<OHOS::HDI::Bluetooth::Hci::V1_0::IHciInterface> impl);

    static int32_t HciInterfaceStubSendHciPacket_(MessageParcel& hciInterfaceData, MessageParcel& hciInterfaceReply, MessageOption& hciInterfaceOption, sptr<OHOS::HDI::Bluetooth::Hci::V1_0::IHciInterface> impl);

    static int32_t HciInterfaceStubClose_(MessageParcel& hciInterfaceData, MessageParcel& hciInterfaceReply, MessageOption& hciInterfaceOption, sptr<OHOS::HDI::Bluetooth::Hci::V1_0::IHciInterface> impl);

    static int32_t HciInterfaceStubGetVersion_(MessageParcel& hciInterfaceData, MessageParcel& hciInterfaceReply, MessageOption& hciInterfaceOption, sptr<OHOS::HDI::Bluetooth::Hci::V1_0::IHciInterface> impl);

private:
    int32_t HciInterfaceStubInit(MessageParcel& hciInterfaceData, MessageParcel& hciInterfaceReply, MessageOption& hciInterfaceOption);

    int32_t HciInterfaceStubSendHciPacket(MessageParcel& hciInterfaceData, MessageParcel& hciInterfaceReply, MessageOption& hciInterfaceOption);

    int32_t HciInterfaceStubClose(MessageParcel& hciInterfaceData, MessageParcel& hciInterfaceReply, MessageOption& hciInterfaceOption);

    int32_t HciInterfaceStubGetVersion(MessageParcel& hciInterfaceData, MessageParcel& hciInterfaceReply, MessageOption& hciInterfaceOption);


    static inline ObjectDelegator<OHOS::HDI::Bluetooth::Hci::V1_0::HciInterfaceStub, OHOS::HDI::Bluetooth::Hci::V1_0::IHciInterface> objDelegator_;
    sptr<OHOS::HDI::Bluetooth::Hci::V1_0::IHciInterface> impl_;
};
} // V1_0
} // Hci
} // Bluetooth
} // HDI
} // OHOS

#endif // OHOS_HDI_BLUETOOTH_HCI_V1_0_HCIINTERFACESTUB_H