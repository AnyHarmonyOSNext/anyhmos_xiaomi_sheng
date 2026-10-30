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

#ifndef OHOS_HDI_BLUETOOTH_HCI_V1_0_IHCIINTERFACE_H
#define OHOS_HDI_BLUETOOTH_HCI_V1_0_IHCIINTERFACE_H

#include <stdint.h>
#include <vector>
#include <hdf_base.h>
#include <hdi_base.h>
#include "bluetooth/hci/v1_0/hci_types.h"
#include "bluetooth/hci/v1_0/ihci_callback.h"

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
namespace Bluetooth {
namespace Hci {
namespace V1_0 {
using namespace OHOS;
using namespace OHOS::HDI;

enum {
    CMD_HCI_INTERFACE_GET_VERSION = 0,
    CMD_HCI_INTERFACE_INIT = 1,
    CMD_HCI_INTERFACE_SEND_HCI_PACKET = 2,
    CMD_HCI_INTERFACE_CLOSE = 3,
};

class IHciInterface : public HdiBase {
public:
    DECLARE_HDI_DESCRIPTOR(u"ohos.hdi.bluetooth.hci.v1_0.IHciInterface");

    virtual ~IHciInterface() = default;

    static sptr<OHOS::HDI::Bluetooth::Hci::V1_0::IHciInterface> Get(bool isStub = false);
    static sptr<OHOS::HDI::Bluetooth::Hci::V1_0::IHciInterface> Get(const std::string &serviceName, bool isStub = false);

    virtual int32_t Init(const sptr<OHOS::HDI::Bluetooth::Hci::V1_0::IHciCallback>& callbackObj) = 0;

    virtual int32_t SendHciPacket(OHOS::HDI::Bluetooth::Hci::V1_0::BtType type, const std::vector<uint8_t>& data) = 0;

    virtual int32_t Close() = 0;

    virtual int32_t GetVersion(uint32_t& majorVer, uint32_t& minorVer)
    {
        majorVer = 1;
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
} // V1_0
} // Hci
} // Bluetooth
} // HDI
} // OHOS

#endif // OHOS_HDI_BLUETOOTH_HCI_V1_0_IHCIINTERFACE_H