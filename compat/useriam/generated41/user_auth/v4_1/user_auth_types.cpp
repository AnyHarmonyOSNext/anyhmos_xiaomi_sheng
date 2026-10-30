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

#include "v4_1/user_auth_types.h"
#include <hdf_core_log.h>
#include <message_parcel.h>
#include <securec.h>

namespace OHOS {
namespace HDI {
namespace UserAuth {
namespace V4_1 {

template<typename ElementType>
static bool ReadPodArray(MessageParcel &parcel, std::vector<ElementType> &data);
template<typename ElementType>
static bool WritePodArray(MessageParcel &parcel, const std::vector<ElementType> &data);


template<typename ElementType>
static bool ReadPodArray(MessageParcel &parcel, std::vector<ElementType> &data)
{
    data.clear();
    uint32_t size = 0;
    if (!parcel.ReadUint32(size)) {
        HDF_LOGE("%{public}s: failed to read size", __func__);
        return false;
    }

    if (size == 0) {
        return true;
    }
    const ElementType *dataPtr = reinterpret_cast<const ElementType*>(parcel.ReadUnpadBuffer(sizeof(ElementType) * size));
    if (dataPtr == nullptr) {
        HDF_LOGI("%{public}s: failed to read data", __func__);
        return false;
    }
    data.assign(dataPtr, dataPtr + size);
    return true;
}

template<typename ElementType>
static bool WritePodArray(MessageParcel &parcel, const std::vector<ElementType> &data)
{
    if (!parcel.WriteUint32(data.size())) {
        HDF_LOGE("%{public}s: failed to write data size", __func__);
        return false;
    }
    if (data.empty()) {
        return true;
    }
    if (!parcel.WriteUnpadBuffer((const void*)data.data(), sizeof(ElementType) * data.size())) {
        HDF_LOGE("%{public}s: failed to write array", __func__);
        return false;
    }
    return true;
}

bool AuthParamExtBlockMarshalling(OHOS::MessageParcel& data, const OHOS::HDI::UserAuth::V4_1::AuthParamExt& dataBlock)
{
    if (!AuthParamBaseBlockMarshalling(data, dataBlock.baseParam)) {
        HDF_LOGE("%{public}s: write dataBlock.baseParam failed!", __func__);
        return false;
    }

    if (!data.WriteInt32(dataBlock.authType)) {
        HDF_LOGE("%{public}s: write dataBlock.authType failed!", __func__);
        return false;
    }

    if (!data.WriteInt32(dataBlock.authIntent)) {
        HDF_LOGE("%{public}s: write dataBlock.authIntent failed!", __func__);
        return false;
    }

    if (!data.WriteBool(dataBlock.isOsAccountVerified)) {
        HDF_LOGE("%{public}s: write dataBlock.isOsAccountVerified failed!", __func__);
        return false;
    }

    if (!data.WriteCString(dataBlock.collectorUdid.c_str())) {
        HDF_LOGE("%{public}s: write dataBlock.collectorUdid failed!", __func__);
        return false;
    }

    if (!WritePodArray(data, dataBlock.credentialIdList)) {
        HDF_LOGE("%{public}s: failed to write dataBlock.credentialIdList", __func__);
        return false;
    }
    return true;
}

bool AuthParamExtBlockUnmarshalling(OHOS::MessageParcel& data, OHOS::HDI::UserAuth::V4_1::AuthParamExt& dataBlock)
{
    if (!OHOS::HDI::UserAuth::V4_0::AuthParamBaseBlockUnmarshalling(data, dataBlock.baseParam)) {
        HDF_LOGE("%{public}s: read dataBlock.baseParam failed!", __func__);
        return false;
    }

    if (!data.ReadInt32(dataBlock.authType)) {
        HDF_LOGE("%{public}s: read dataBlock.authType failed!", __func__);
        return false;
    }

    if (!data.ReadInt32(dataBlock.authIntent)) {
        HDF_LOGE("%{public}s: read dataBlock.authIntent failed!", __func__);
        return false;
    }

    if (!data.ReadBool(dataBlock.isOsAccountVerified)) {
        HDF_LOGE("%{public}s: read dataBlock.isOsAccountVerified failed!", __func__);
        return false;
    }

    const char* collectorUdidCp = data.ReadCString();
    if (collectorUdidCp == nullptr) {
        HDF_LOGE("%{public}s: read collectorUdidCp failed", __func__);
        return false;
    }
    dataBlock.collectorUdid = collectorUdidCp;

    if (!ReadPodArray(data, dataBlock.credentialIdList)) {
        HDF_LOGE("%{public}s: failed to read dataBlock.credentialIdList", __func__);
        return false;
    }
    return true;
}

bool EnrollParamExtBlockMarshalling(OHOS::MessageParcel& data, const OHOS::HDI::UserAuth::V4_1::EnrollParamExt& dataBlock)
{
    if (!data.WriteInt32(dataBlock.authType)) {
        HDF_LOGE("%{public}s: write dataBlock.authType failed!", __func__);
        return false;
    }

    if (!data.WriteUint32(dataBlock.executorSensorHint)) {
        HDF_LOGE("%{public}s: write dataBlock.executorSensorHint failed!", __func__);
        return false;
    }

    if (!data.WriteCString(dataBlock.callerName.c_str())) {
        HDF_LOGE("%{public}s: write dataBlock.callerName failed!", __func__);
        return false;
    }

    if (!data.WriteInt32(dataBlock.callerType)) {
        HDF_LOGE("%{public}s: write dataBlock.callerType failed!", __func__);
        return false;
    }

    if (!data.WriteInt32(dataBlock.apiVersion)) {
        HDF_LOGE("%{public}s: write dataBlock.apiVersion failed!", __func__);
        return false;
    }

    if (!data.WriteInt32(dataBlock.userId)) {
        HDF_LOGE("%{public}s: write dataBlock.userId failed!", __func__);
        return false;
    }

    if (!data.WriteInt32(dataBlock.userType)) {
        HDF_LOGE("%{public}s: write dataBlock.userType failed!", __func__);
        return false;
    }

    if (!data.WriteInt32(dataBlock.authSubType)) {
        HDF_LOGE("%{public}s: write dataBlock.authSubType failed!", __func__);
        return false;
    }

    if (!data.WriteCString(dataBlock.additionalInfo.c_str())) {
        HDF_LOGE("%{public}s: write dataBlock.additionalInfo failed!", __func__);
        return false;
    }
    return true;
}

bool EnrollParamExtBlockUnmarshalling(OHOS::MessageParcel& data, OHOS::HDI::UserAuth::V4_1::EnrollParamExt& dataBlock)
{
    if (!data.ReadInt32(dataBlock.authType)) {
        HDF_LOGE("%{public}s: read dataBlock.authType failed!", __func__);
        return false;
    }

    if (!data.ReadUint32(dataBlock.executorSensorHint)) {
        HDF_LOGE("%{public}s: read dataBlock.executorSensorHint failed!", __func__);
        return false;
    }

    const char* callerNameCp = data.ReadCString();
    if (callerNameCp == nullptr) {
        HDF_LOGE("%{public}s: read callerNameCp failed", __func__);
        return false;
    }
    dataBlock.callerName = callerNameCp;

    if (!data.ReadInt32(dataBlock.callerType)) {
        HDF_LOGE("%{public}s: read dataBlock.callerType failed!", __func__);
        return false;
    }

    if (!data.ReadInt32(dataBlock.apiVersion)) {
        HDF_LOGE("%{public}s: read dataBlock.apiVersion failed!", __func__);
        return false;
    }

    if (!data.ReadInt32(dataBlock.userId)) {
        HDF_LOGE("%{public}s: read dataBlock.userId failed!", __func__);
        return false;
    }

    if (!data.ReadInt32(dataBlock.userType)) {
        HDF_LOGE("%{public}s: read dataBlock.userType failed!", __func__);
        return false;
    }

    if (!data.ReadInt32(dataBlock.authSubType)) {
        HDF_LOGE("%{public}s: read dataBlock.authSubType failed!", __func__);
        return false;
    }

    const char* additionalInfoCp = data.ReadCString();
    if (additionalInfoCp == nullptr) {
        HDF_LOGE("%{public}s: read additionalInfoCp failed", __func__);
        return false;
    }
    dataBlock.additionalInfo = additionalInfoCp;
    return true;
}

} // V4_1
} // UserAuth
} // HDI
} // OHOS
