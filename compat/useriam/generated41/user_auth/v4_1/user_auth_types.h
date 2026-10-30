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

#ifndef OHOS_HDI_USER_AUTH_V4_1_USERAUTHTYPES_H
#define OHOS_HDI_USER_AUTH_V4_1_USERAUTHTYPES_H

#include <cstdbool>
#include <cstdint>
#include <string>
#include <vector>
#include "user_auth/v4_0/user_auth_types.h"

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
class MessageParcel;
}

namespace OHOS {
namespace HDI {
namespace UserAuth {
namespace V4_1 {

using namespace OHOS;
using namespace OHOS::HDI::UserAuth::V4_0;

struct AuthParamExt {
    OHOS::HDI::UserAuth::V4_0::AuthParamBase baseParam;
    int32_t authType;
    int32_t authIntent;
    bool isOsAccountVerified;
    std::string collectorUdid;
    std::vector<uint64_t> credentialIdList;
};

struct EnrollParamExt {
    int32_t authType;
    uint32_t executorSensorHint;
    std::string callerName;
    int32_t callerType;
    int32_t apiVersion;
    int32_t userId;
    int32_t userType;
    int32_t authSubType;
    std::string additionalInfo;
};

bool AuthParamExtBlockMarshalling(OHOS::MessageParcel &data, const OHOS::HDI::UserAuth::V4_1::AuthParamExt& dataBlock);

bool AuthParamExtBlockUnmarshalling(OHOS::MessageParcel &data, OHOS::HDI::UserAuth::V4_1::AuthParamExt& dataBlock);

bool EnrollParamExtBlockMarshalling(OHOS::MessageParcel &data, const OHOS::HDI::UserAuth::V4_1::EnrollParamExt& dataBlock);

bool EnrollParamExtBlockUnmarshalling(OHOS::MessageParcel &data, OHOS::HDI::UserAuth::V4_1::EnrollParamExt& dataBlock);

} // V4_1
} // UserAuth
} // HDI
} // OHOS

#endif // OHOS_HDI_USER_AUTH_V4_1_USERAUTHTYPES_H