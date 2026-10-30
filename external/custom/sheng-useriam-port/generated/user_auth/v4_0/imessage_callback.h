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

#ifndef OHOS_HDI_USER_AUTH_V4_0_IMESSAGECALLBACK_H
#define OHOS_HDI_USER_AUTH_V4_0_IMESSAGECALLBACK_H

#include <stdint.h>
#include <vector>
#include <hdf_base.h>
#include <hdi_base.h>

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
namespace UserAuth {
namespace V4_0 {
using namespace OHOS;
using namespace OHOS::HDI;

enum {
    CMD_MESSAGE_CALLBACK_GET_VERSION = 0,
    CMD_MESSAGE_CALLBACK_ON_MESSAGE = 1,
};

class IMessageCallback : public HdiBase {
public:
    DECLARE_HDI_DESCRIPTOR(u"ohos.hdi.user_auth.v4_0.IMessageCallback");

    virtual ~IMessageCallback() = default;

    virtual int32_t OnMessage(uint64_t scheduleId, int32_t destRole, const std::vector<uint8_t>& msg) = 0;

    virtual int32_t GetVersion(uint32_t& majorVer, uint32_t& minorVer)
    {
        majorVer = 4;
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
} // V4_0
} // UserAuth
} // HDI
} // OHOS

#endif // OHOS_HDI_USER_AUTH_V4_0_IMESSAGECALLBACK_H