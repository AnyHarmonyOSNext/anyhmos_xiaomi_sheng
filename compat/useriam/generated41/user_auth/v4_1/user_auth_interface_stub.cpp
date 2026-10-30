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

#include "v4_1/user_auth_interface_stub.h"
#include <hdf_base.h>
#include <hdf_core_log.h>
#include <hdi_support.h>
#include <securec.h>
#include <string_ex.h>

#define HDF_LOG_TAG    user_auth_interface_stub

namespace OHOS {
namespace HDI {
namespace UserAuth {
namespace V4_1 {
template<typename ElementType>
static bool ReadPodArray(MessageParcel &parcel, std::vector<ElementType> &data);


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

sptr<OHOS::HDI::UserAuth::V4_1::IUserAuthInterface> OHOS::HDI::UserAuth::V4_1::IUserAuthInterface::Get(bool isStub)
{
    return OHOS::HDI::UserAuth::V4_1::IUserAuthInterface::Get("user_auth_interface_service", isStub);
}

sptr<OHOS::HDI::UserAuth::V4_1::IUserAuthInterface> OHOS::HDI::UserAuth::V4_1::IUserAuthInterface::Get(const std::string& serviceName, bool isStub)
{
    if (!isStub) {
        return nullptr;
    }
    std::string desc = Str16ToStr8(OHOS::HDI::UserAuth::V4_1::IUserAuthInterface::GetDescriptor());
    void *impl = LoadHdiImpl(desc.c_str(), serviceName == "user_auth_interface_service" ? "service" : serviceName.c_str());
    if (impl == nullptr) {
        HDF_LOGE("failed to load hdi impl %{public}s", desc.c_str());
        return nullptr;
    }
    return reinterpret_cast<OHOS::HDI::UserAuth::V4_1::IUserAuthInterface *>(impl);
}


OHOS::HDI::UserAuth::V4_1::UserAuthInterfaceStub::UserAuthInterfaceStub(const sptr<OHOS::HDI::UserAuth::V4_1::IUserAuthInterface> &impl)
    : IPCObjectStub(OHOS::HDI::UserAuth::V4_1::IUserAuthInterface::GetDescriptor()), impl_(impl)
{
}

OHOS::HDI::UserAuth::V4_1::UserAuthInterfaceStub::~UserAuthInterfaceStub()
{
    HDF_LOGI("%{public}s enter", __func__);
    ObjectCollector::GetInstance().RemoveObject(impl_);
}

int32_t OHOS::HDI::UserAuth::V4_1::UserAuthInterfaceStub::OnRemoteRequest(uint32_t code, MessageParcel& data, MessageParcel& reply, MessageOption& option)
{
    switch (code) {
        case CMD_USER_AUTH_INTERFACE_GET_VERSION:
            return UserAuthInterfaceStubGetVersion(data, reply, option);
        case CMD_USER_AUTH_INTERFACE_BEGIN_AUTHENTICATION_EXT:
            return UserAuthInterfaceStubBeginAuthenticationExt(data, reply, option);
        case CMD_USER_AUTH_INTERFACE_BEGIN_ENROLLMENT_EXT:
            return UserAuthInterfaceStubBeginEnrollmentExt(data, reply, option);
        case CMD_USER_AUTH_INTERFACE_INIT:
            return UserAuthInterfaceStubInit(data, reply, option);
        case CMD_USER_AUTH_INTERFACE_ADD_EXECUTOR:
            return UserAuthInterfaceStubAddExecutor(data, reply, option);
        case CMD_USER_AUTH_INTERFACE_DELETE_EXECUTOR:
            return UserAuthInterfaceStubDeleteExecutor(data, reply, option);
        case CMD_USER_AUTH_INTERFACE_OPEN_SESSION:
            return UserAuthInterfaceStubOpenSession(data, reply, option);
        case CMD_USER_AUTH_INTERFACE_CLOSE_SESSION:
            return UserAuthInterfaceStubCloseSession(data, reply, option);
        case CMD_USER_AUTH_INTERFACE_UPDATE_ENROLLMENT_RESULT:
            return UserAuthInterfaceStubUpdateEnrollmentResult(data, reply, option);
        case CMD_USER_AUTH_INTERFACE_CANCEL_ENROLLMENT:
            return UserAuthInterfaceStubCancelEnrollment(data, reply, option);
        case CMD_USER_AUTH_INTERFACE_DELETE_CREDENTIAL:
            return UserAuthInterfaceStubDeleteCredential(data, reply, option);
        case CMD_USER_AUTH_INTERFACE_GET_CREDENTIAL:
            return UserAuthInterfaceStubGetCredential(data, reply, option);
        case CMD_USER_AUTH_INTERFACE_GET_USER_INFO:
            return UserAuthInterfaceStubGetUserInfo(data, reply, option);
        case CMD_USER_AUTH_INTERFACE_DELETE_USER:
            return UserAuthInterfaceStubDeleteUser(data, reply, option);
        case CMD_USER_AUTH_INTERFACE_ENFORCE_DELETE_USER:
            return UserAuthInterfaceStubEnforceDeleteUser(data, reply, option);
        case CMD_USER_AUTH_INTERFACE_UPDATE_AUTHENTICATION_RESULT:
            return UserAuthInterfaceStubUpdateAuthenticationResult(data, reply, option);
        case CMD_USER_AUTH_INTERFACE_CANCEL_AUTHENTICATION:
            return UserAuthInterfaceStubCancelAuthentication(data, reply, option);
        case CMD_USER_AUTH_INTERFACE_UPDATE_IDENTIFICATION_RESULT:
            return UserAuthInterfaceStubUpdateIdentificationResult(data, reply, option);
        case CMD_USER_AUTH_INTERFACE_CANCEL_IDENTIFICATION:
            return UserAuthInterfaceStubCancelIdentification(data, reply, option);
        case CMD_USER_AUTH_INTERFACE_GET_AVAILABLE_STATUS:
            return UserAuthInterfaceStubGetAvailableStatus(data, reply, option);
        case CMD_USER_AUTH_INTERFACE_GET_VALID_SOLUTION:
            return UserAuthInterfaceStubGetValidSolution(data, reply, option);
        case CMD_USER_AUTH_INTERFACE_BEGIN_AUTHENTICATION:
            return UserAuthInterfaceStubBeginAuthentication(data, reply, option);
        case CMD_USER_AUTH_INTERFACE_BEGIN_ENROLLMENT:
            return UserAuthInterfaceStubBeginEnrollment(data, reply, option);
        case CMD_USER_AUTH_INTERFACE_BEGIN_IDENTIFICATION:
            return UserAuthInterfaceStubBeginIdentification(data, reply, option);
        case CMD_USER_AUTH_INTERFACE_GET_ALL_USER_INFO:
            return UserAuthInterfaceStubGetAllUserInfo(data, reply, option);
        case CMD_USER_AUTH_INTERFACE_GET_ALL_EXT_USER_INFO:
            return UserAuthInterfaceStubGetAllExtUserInfo(data, reply, option);
        case CMD_USER_AUTH_INTERFACE_GET_ENROLLED_STATE:
            return UserAuthInterfaceStubGetEnrolledState(data, reply, option);
        case CMD_USER_AUTH_INTERFACE_CHECK_REUSE_UNLOCK_RESULT:
            return UserAuthInterfaceStubCheckReuseUnlockResult(data, reply, option);
        case CMD_USER_AUTH_INTERFACE_SEND_MESSAGE:
            return UserAuthInterfaceStubSendMessage(data, reply, option);
        case CMD_USER_AUTH_INTERFACE_REGISTER_MESSAGE_CALLBACK:
            return UserAuthInterfaceStubRegisterMessageCallback(data, reply, option);
        case CMD_USER_AUTH_INTERFACE_PREPARE_REMOTE_AUTH:
            return UserAuthInterfaceStubPrepareRemoteAuth(data, reply, option);
        case CMD_USER_AUTH_INTERFACE_GET_LOCAL_SCHEDULE_FROM_MESSAGE:
            return UserAuthInterfaceStubGetLocalScheduleFromMessage(data, reply, option);
        case CMD_USER_AUTH_INTERFACE_GET_SIGNED_EXECUTOR_INFO:
            return UserAuthInterfaceStubGetSignedExecutorInfo(data, reply, option);
        case CMD_USER_AUTH_INTERFACE_GET_AUTH_RESULT_FROM_MESSAGE:
            return UserAuthInterfaceStubGetAuthResultFromMessage(data, reply, option);
        case CMD_USER_AUTH_INTERFACE_SET_GLOBAL_CONFIG_PARAM:
            return UserAuthInterfaceStubSetGlobalConfigParam(data, reply, option);
        case CMD_USER_AUTH_INTERFACE_GET_CREDENTIAL_BY_ID:
            return UserAuthInterfaceStubGetCredentialById(data, reply, option);
        case CMD_USER_AUTH_INTERFACE_VERIFY_AUTH_TOKEN:
            return UserAuthInterfaceStubVerifyAuthToken(data, reply, option);
        case CMD_USER_AUTH_INTERFACE_UPDATE_ABANDON_RESULT:
            return UserAuthInterfaceStubUpdateAbandonResult(data, reply, option);
        case CMD_USER_AUTH_INTERFACE_CLEAR_UNAVAILABLE_CREDENTIAL:
            return UserAuthInterfaceStubClearUnavailableCredential(data, reply, option);
        default: {
            HDF_LOGE("%{public}s: cmd %{public}d is not supported", __func__, code);
            return IPCObjectStub::OnRemoteRequest(code, data, reply, option);
        }
    }
}

int32_t OHOS::HDI::UserAuth::V4_1::UserAuthInterfaceStub::UserAuthInterfaceStubBeginAuthenticationExt(MessageParcel& userAuthInterfaceData, MessageParcel& userAuthInterfaceReply, MessageOption& userAuthInterfaceOption)
{
    return OHOS::HDI::UserAuth::V4_1::UserAuthInterfaceStub::UserAuthInterfaceStubBeginAuthenticationExt_(userAuthInterfaceData, userAuthInterfaceReply, userAuthInterfaceOption, impl_);
}

int32_t OHOS::HDI::UserAuth::V4_1::UserAuthInterfaceStub::UserAuthInterfaceStubBeginEnrollmentExt(MessageParcel& userAuthInterfaceData, MessageParcel& userAuthInterfaceReply, MessageOption& userAuthInterfaceOption)
{
    return OHOS::HDI::UserAuth::V4_1::UserAuthInterfaceStub::UserAuthInterfaceStubBeginEnrollmentExt_(userAuthInterfaceData, userAuthInterfaceReply, userAuthInterfaceOption, impl_);
}

int32_t OHOS::HDI::UserAuth::V4_1::UserAuthInterfaceStub::UserAuthInterfaceStubInit(MessageParcel& userAuthInterfaceData, MessageParcel& userAuthInterfaceReply, MessageOption& userAuthInterfaceOption)
{
    return OHOS::HDI::UserAuth::V4_0::UserAuthInterfaceStub::UserAuthInterfaceStubInit_(userAuthInterfaceData, userAuthInterfaceReply, userAuthInterfaceOption, impl_);
}

int32_t OHOS::HDI::UserAuth::V4_1::UserAuthInterfaceStub::UserAuthInterfaceStubAddExecutor(MessageParcel& userAuthInterfaceData, MessageParcel& userAuthInterfaceReply, MessageOption& userAuthInterfaceOption)
{
    return OHOS::HDI::UserAuth::V4_0::UserAuthInterfaceStub::UserAuthInterfaceStubAddExecutor_(userAuthInterfaceData, userAuthInterfaceReply, userAuthInterfaceOption, impl_);
}

int32_t OHOS::HDI::UserAuth::V4_1::UserAuthInterfaceStub::UserAuthInterfaceStubDeleteExecutor(MessageParcel& userAuthInterfaceData, MessageParcel& userAuthInterfaceReply, MessageOption& userAuthInterfaceOption)
{
    return OHOS::HDI::UserAuth::V4_0::UserAuthInterfaceStub::UserAuthInterfaceStubDeleteExecutor_(userAuthInterfaceData, userAuthInterfaceReply, userAuthInterfaceOption, impl_);
}

int32_t OHOS::HDI::UserAuth::V4_1::UserAuthInterfaceStub::UserAuthInterfaceStubOpenSession(MessageParcel& userAuthInterfaceData, MessageParcel& userAuthInterfaceReply, MessageOption& userAuthInterfaceOption)
{
    return OHOS::HDI::UserAuth::V4_0::UserAuthInterfaceStub::UserAuthInterfaceStubOpenSession_(userAuthInterfaceData, userAuthInterfaceReply, userAuthInterfaceOption, impl_);
}

int32_t OHOS::HDI::UserAuth::V4_1::UserAuthInterfaceStub::UserAuthInterfaceStubCloseSession(MessageParcel& userAuthInterfaceData, MessageParcel& userAuthInterfaceReply, MessageOption& userAuthInterfaceOption)
{
    return OHOS::HDI::UserAuth::V4_0::UserAuthInterfaceStub::UserAuthInterfaceStubCloseSession_(userAuthInterfaceData, userAuthInterfaceReply, userAuthInterfaceOption, impl_);
}

int32_t OHOS::HDI::UserAuth::V4_1::UserAuthInterfaceStub::UserAuthInterfaceStubUpdateEnrollmentResult(MessageParcel& userAuthInterfaceData, MessageParcel& userAuthInterfaceReply, MessageOption& userAuthInterfaceOption)
{
    return OHOS::HDI::UserAuth::V4_0::UserAuthInterfaceStub::UserAuthInterfaceStubUpdateEnrollmentResult_(userAuthInterfaceData, userAuthInterfaceReply, userAuthInterfaceOption, impl_);
}

int32_t OHOS::HDI::UserAuth::V4_1::UserAuthInterfaceStub::UserAuthInterfaceStubCancelEnrollment(MessageParcel& userAuthInterfaceData, MessageParcel& userAuthInterfaceReply, MessageOption& userAuthInterfaceOption)
{
    return OHOS::HDI::UserAuth::V4_0::UserAuthInterfaceStub::UserAuthInterfaceStubCancelEnrollment_(userAuthInterfaceData, userAuthInterfaceReply, userAuthInterfaceOption, impl_);
}

int32_t OHOS::HDI::UserAuth::V4_1::UserAuthInterfaceStub::UserAuthInterfaceStubDeleteCredential(MessageParcel& userAuthInterfaceData, MessageParcel& userAuthInterfaceReply, MessageOption& userAuthInterfaceOption)
{
    return OHOS::HDI::UserAuth::V4_0::UserAuthInterfaceStub::UserAuthInterfaceStubDeleteCredential_(userAuthInterfaceData, userAuthInterfaceReply, userAuthInterfaceOption, impl_);
}

int32_t OHOS::HDI::UserAuth::V4_1::UserAuthInterfaceStub::UserAuthInterfaceStubGetCredential(MessageParcel& userAuthInterfaceData, MessageParcel& userAuthInterfaceReply, MessageOption& userAuthInterfaceOption)
{
    return OHOS::HDI::UserAuth::V4_0::UserAuthInterfaceStub::UserAuthInterfaceStubGetCredential_(userAuthInterfaceData, userAuthInterfaceReply, userAuthInterfaceOption, impl_);
}

int32_t OHOS::HDI::UserAuth::V4_1::UserAuthInterfaceStub::UserAuthInterfaceStubGetUserInfo(MessageParcel& userAuthInterfaceData, MessageParcel& userAuthInterfaceReply, MessageOption& userAuthInterfaceOption)
{
    return OHOS::HDI::UserAuth::V4_0::UserAuthInterfaceStub::UserAuthInterfaceStubGetUserInfo_(userAuthInterfaceData, userAuthInterfaceReply, userAuthInterfaceOption, impl_);
}

int32_t OHOS::HDI::UserAuth::V4_1::UserAuthInterfaceStub::UserAuthInterfaceStubDeleteUser(MessageParcel& userAuthInterfaceData, MessageParcel& userAuthInterfaceReply, MessageOption& userAuthInterfaceOption)
{
    return OHOS::HDI::UserAuth::V4_0::UserAuthInterfaceStub::UserAuthInterfaceStubDeleteUser_(userAuthInterfaceData, userAuthInterfaceReply, userAuthInterfaceOption, impl_);
}

int32_t OHOS::HDI::UserAuth::V4_1::UserAuthInterfaceStub::UserAuthInterfaceStubEnforceDeleteUser(MessageParcel& userAuthInterfaceData, MessageParcel& userAuthInterfaceReply, MessageOption& userAuthInterfaceOption)
{
    return OHOS::HDI::UserAuth::V4_0::UserAuthInterfaceStub::UserAuthInterfaceStubEnforceDeleteUser_(userAuthInterfaceData, userAuthInterfaceReply, userAuthInterfaceOption, impl_);
}

int32_t OHOS::HDI::UserAuth::V4_1::UserAuthInterfaceStub::UserAuthInterfaceStubUpdateAuthenticationResult(MessageParcel& userAuthInterfaceData, MessageParcel& userAuthInterfaceReply, MessageOption& userAuthInterfaceOption)
{
    return OHOS::HDI::UserAuth::V4_0::UserAuthInterfaceStub::UserAuthInterfaceStubUpdateAuthenticationResult_(userAuthInterfaceData, userAuthInterfaceReply, userAuthInterfaceOption, impl_);
}

int32_t OHOS::HDI::UserAuth::V4_1::UserAuthInterfaceStub::UserAuthInterfaceStubCancelAuthentication(MessageParcel& userAuthInterfaceData, MessageParcel& userAuthInterfaceReply, MessageOption& userAuthInterfaceOption)
{
    return OHOS::HDI::UserAuth::V4_0::UserAuthInterfaceStub::UserAuthInterfaceStubCancelAuthentication_(userAuthInterfaceData, userAuthInterfaceReply, userAuthInterfaceOption, impl_);
}

int32_t OHOS::HDI::UserAuth::V4_1::UserAuthInterfaceStub::UserAuthInterfaceStubUpdateIdentificationResult(MessageParcel& userAuthInterfaceData, MessageParcel& userAuthInterfaceReply, MessageOption& userAuthInterfaceOption)
{
    return OHOS::HDI::UserAuth::V4_0::UserAuthInterfaceStub::UserAuthInterfaceStubUpdateIdentificationResult_(userAuthInterfaceData, userAuthInterfaceReply, userAuthInterfaceOption, impl_);
}

int32_t OHOS::HDI::UserAuth::V4_1::UserAuthInterfaceStub::UserAuthInterfaceStubCancelIdentification(MessageParcel& userAuthInterfaceData, MessageParcel& userAuthInterfaceReply, MessageOption& userAuthInterfaceOption)
{
    return OHOS::HDI::UserAuth::V4_0::UserAuthInterfaceStub::UserAuthInterfaceStubCancelIdentification_(userAuthInterfaceData, userAuthInterfaceReply, userAuthInterfaceOption, impl_);
}

int32_t OHOS::HDI::UserAuth::V4_1::UserAuthInterfaceStub::UserAuthInterfaceStubGetAvailableStatus(MessageParcel& userAuthInterfaceData, MessageParcel& userAuthInterfaceReply, MessageOption& userAuthInterfaceOption)
{
    return OHOS::HDI::UserAuth::V4_0::UserAuthInterfaceStub::UserAuthInterfaceStubGetAvailableStatus_(userAuthInterfaceData, userAuthInterfaceReply, userAuthInterfaceOption, impl_);
}

int32_t OHOS::HDI::UserAuth::V4_1::UserAuthInterfaceStub::UserAuthInterfaceStubGetValidSolution(MessageParcel& userAuthInterfaceData, MessageParcel& userAuthInterfaceReply, MessageOption& userAuthInterfaceOption)
{
    return OHOS::HDI::UserAuth::V4_0::UserAuthInterfaceStub::UserAuthInterfaceStubGetValidSolution_(userAuthInterfaceData, userAuthInterfaceReply, userAuthInterfaceOption, impl_);
}

int32_t OHOS::HDI::UserAuth::V4_1::UserAuthInterfaceStub::UserAuthInterfaceStubBeginAuthentication(MessageParcel& userAuthInterfaceData, MessageParcel& userAuthInterfaceReply, MessageOption& userAuthInterfaceOption)
{
    return OHOS::HDI::UserAuth::V4_0::UserAuthInterfaceStub::UserAuthInterfaceStubBeginAuthentication_(userAuthInterfaceData, userAuthInterfaceReply, userAuthInterfaceOption, impl_);
}

int32_t OHOS::HDI::UserAuth::V4_1::UserAuthInterfaceStub::UserAuthInterfaceStubBeginEnrollment(MessageParcel& userAuthInterfaceData, MessageParcel& userAuthInterfaceReply, MessageOption& userAuthInterfaceOption)
{
    return OHOS::HDI::UserAuth::V4_0::UserAuthInterfaceStub::UserAuthInterfaceStubBeginEnrollment_(userAuthInterfaceData, userAuthInterfaceReply, userAuthInterfaceOption, impl_);
}

int32_t OHOS::HDI::UserAuth::V4_1::UserAuthInterfaceStub::UserAuthInterfaceStubBeginIdentification(MessageParcel& userAuthInterfaceData, MessageParcel& userAuthInterfaceReply, MessageOption& userAuthInterfaceOption)
{
    return OHOS::HDI::UserAuth::V4_0::UserAuthInterfaceStub::UserAuthInterfaceStubBeginIdentification_(userAuthInterfaceData, userAuthInterfaceReply, userAuthInterfaceOption, impl_);
}

int32_t OHOS::HDI::UserAuth::V4_1::UserAuthInterfaceStub::UserAuthInterfaceStubGetAllUserInfo(MessageParcel& userAuthInterfaceData, MessageParcel& userAuthInterfaceReply, MessageOption& userAuthInterfaceOption)
{
    return OHOS::HDI::UserAuth::V4_0::UserAuthInterfaceStub::UserAuthInterfaceStubGetAllUserInfo_(userAuthInterfaceData, userAuthInterfaceReply, userAuthInterfaceOption, impl_);
}

int32_t OHOS::HDI::UserAuth::V4_1::UserAuthInterfaceStub::UserAuthInterfaceStubGetAllExtUserInfo(MessageParcel& userAuthInterfaceData, MessageParcel& userAuthInterfaceReply, MessageOption& userAuthInterfaceOption)
{
    return OHOS::HDI::UserAuth::V4_0::UserAuthInterfaceStub::UserAuthInterfaceStubGetAllExtUserInfo_(userAuthInterfaceData, userAuthInterfaceReply, userAuthInterfaceOption, impl_);
}

int32_t OHOS::HDI::UserAuth::V4_1::UserAuthInterfaceStub::UserAuthInterfaceStubGetEnrolledState(MessageParcel& userAuthInterfaceData, MessageParcel& userAuthInterfaceReply, MessageOption& userAuthInterfaceOption)
{
    return OHOS::HDI::UserAuth::V4_0::UserAuthInterfaceStub::UserAuthInterfaceStubGetEnrolledState_(userAuthInterfaceData, userAuthInterfaceReply, userAuthInterfaceOption, impl_);
}

int32_t OHOS::HDI::UserAuth::V4_1::UserAuthInterfaceStub::UserAuthInterfaceStubCheckReuseUnlockResult(MessageParcel& userAuthInterfaceData, MessageParcel& userAuthInterfaceReply, MessageOption& userAuthInterfaceOption)
{
    return OHOS::HDI::UserAuth::V4_0::UserAuthInterfaceStub::UserAuthInterfaceStubCheckReuseUnlockResult_(userAuthInterfaceData, userAuthInterfaceReply, userAuthInterfaceOption, impl_);
}

int32_t OHOS::HDI::UserAuth::V4_1::UserAuthInterfaceStub::UserAuthInterfaceStubSendMessage(MessageParcel& userAuthInterfaceData, MessageParcel& userAuthInterfaceReply, MessageOption& userAuthInterfaceOption)
{
    return OHOS::HDI::UserAuth::V4_0::UserAuthInterfaceStub::UserAuthInterfaceStubSendMessage_(userAuthInterfaceData, userAuthInterfaceReply, userAuthInterfaceOption, impl_);
}

int32_t OHOS::HDI::UserAuth::V4_1::UserAuthInterfaceStub::UserAuthInterfaceStubRegisterMessageCallback(MessageParcel& userAuthInterfaceData, MessageParcel& userAuthInterfaceReply, MessageOption& userAuthInterfaceOption)
{
    return OHOS::HDI::UserAuth::V4_0::UserAuthInterfaceStub::UserAuthInterfaceStubRegisterMessageCallback_(userAuthInterfaceData, userAuthInterfaceReply, userAuthInterfaceOption, impl_);
}

int32_t OHOS::HDI::UserAuth::V4_1::UserAuthInterfaceStub::UserAuthInterfaceStubPrepareRemoteAuth(MessageParcel& userAuthInterfaceData, MessageParcel& userAuthInterfaceReply, MessageOption& userAuthInterfaceOption)
{
    return OHOS::HDI::UserAuth::V4_0::UserAuthInterfaceStub::UserAuthInterfaceStubPrepareRemoteAuth_(userAuthInterfaceData, userAuthInterfaceReply, userAuthInterfaceOption, impl_);
}

int32_t OHOS::HDI::UserAuth::V4_1::UserAuthInterfaceStub::UserAuthInterfaceStubGetLocalScheduleFromMessage(MessageParcel& userAuthInterfaceData, MessageParcel& userAuthInterfaceReply, MessageOption& userAuthInterfaceOption)
{
    return OHOS::HDI::UserAuth::V4_0::UserAuthInterfaceStub::UserAuthInterfaceStubGetLocalScheduleFromMessage_(userAuthInterfaceData, userAuthInterfaceReply, userAuthInterfaceOption, impl_);
}

int32_t OHOS::HDI::UserAuth::V4_1::UserAuthInterfaceStub::UserAuthInterfaceStubGetSignedExecutorInfo(MessageParcel& userAuthInterfaceData, MessageParcel& userAuthInterfaceReply, MessageOption& userAuthInterfaceOption)
{
    return OHOS::HDI::UserAuth::V4_0::UserAuthInterfaceStub::UserAuthInterfaceStubGetSignedExecutorInfo_(userAuthInterfaceData, userAuthInterfaceReply, userAuthInterfaceOption, impl_);
}

int32_t OHOS::HDI::UserAuth::V4_1::UserAuthInterfaceStub::UserAuthInterfaceStubGetAuthResultFromMessage(MessageParcel& userAuthInterfaceData, MessageParcel& userAuthInterfaceReply, MessageOption& userAuthInterfaceOption)
{
    return OHOS::HDI::UserAuth::V4_0::UserAuthInterfaceStub::UserAuthInterfaceStubGetAuthResultFromMessage_(userAuthInterfaceData, userAuthInterfaceReply, userAuthInterfaceOption, impl_);
}

int32_t OHOS::HDI::UserAuth::V4_1::UserAuthInterfaceStub::UserAuthInterfaceStubSetGlobalConfigParam(MessageParcel& userAuthInterfaceData, MessageParcel& userAuthInterfaceReply, MessageOption& userAuthInterfaceOption)
{
    return OHOS::HDI::UserAuth::V4_0::UserAuthInterfaceStub::UserAuthInterfaceStubSetGlobalConfigParam_(userAuthInterfaceData, userAuthInterfaceReply, userAuthInterfaceOption, impl_);
}

int32_t OHOS::HDI::UserAuth::V4_1::UserAuthInterfaceStub::UserAuthInterfaceStubGetCredentialById(MessageParcel& userAuthInterfaceData, MessageParcel& userAuthInterfaceReply, MessageOption& userAuthInterfaceOption)
{
    return OHOS::HDI::UserAuth::V4_0::UserAuthInterfaceStub::UserAuthInterfaceStubGetCredentialById_(userAuthInterfaceData, userAuthInterfaceReply, userAuthInterfaceOption, impl_);
}

int32_t OHOS::HDI::UserAuth::V4_1::UserAuthInterfaceStub::UserAuthInterfaceStubVerifyAuthToken(MessageParcel& userAuthInterfaceData, MessageParcel& userAuthInterfaceReply, MessageOption& userAuthInterfaceOption)
{
    return OHOS::HDI::UserAuth::V4_0::UserAuthInterfaceStub::UserAuthInterfaceStubVerifyAuthToken_(userAuthInterfaceData, userAuthInterfaceReply, userAuthInterfaceOption, impl_);
}

int32_t OHOS::HDI::UserAuth::V4_1::UserAuthInterfaceStub::UserAuthInterfaceStubUpdateAbandonResult(MessageParcel& userAuthInterfaceData, MessageParcel& userAuthInterfaceReply, MessageOption& userAuthInterfaceOption)
{
    return OHOS::HDI::UserAuth::V4_0::UserAuthInterfaceStub::UserAuthInterfaceStubUpdateAbandonResult_(userAuthInterfaceData, userAuthInterfaceReply, userAuthInterfaceOption, impl_);
}

int32_t OHOS::HDI::UserAuth::V4_1::UserAuthInterfaceStub::UserAuthInterfaceStubClearUnavailableCredential(MessageParcel& userAuthInterfaceData, MessageParcel& userAuthInterfaceReply, MessageOption& userAuthInterfaceOption)
{
    return OHOS::HDI::UserAuth::V4_0::UserAuthInterfaceStub::UserAuthInterfaceStubClearUnavailableCredential_(userAuthInterfaceData, userAuthInterfaceReply, userAuthInterfaceOption, impl_);
}

int32_t OHOS::HDI::UserAuth::V4_1::UserAuthInterfaceStub::UserAuthInterfaceStubGetVersion(MessageParcel& userAuthInterfaceData, MessageParcel& userAuthInterfaceReply, MessageOption& userAuthInterfaceOption)
{
    return OHOS::HDI::UserAuth::V4_0::UserAuthInterfaceStub::UserAuthInterfaceStubGetVersion_(userAuthInterfaceData, userAuthInterfaceReply, userAuthInterfaceOption, impl_);
}

int32_t OHOS::HDI::UserAuth::V4_1::UserAuthInterfaceStub::UserAuthInterfaceStubBeginAuthenticationExt_(MessageParcel& userAuthInterfaceData, MessageParcel& userAuthInterfaceReply, MessageOption& userAuthInterfaceOption, sptr<OHOS::HDI::UserAuth::V4_1::IUserAuthInterface> impl)
{
    if (userAuthInterfaceData.ReadInterfaceToken() != OHOS::HDI::UserAuth::V4_1::IUserAuthInterface::GetDescriptor()) {
        HDF_LOGE("%{public}s: interface token check failed!", __func__);
        return HDF_ERR_INVALID_PARAM;
    }

    bool userAuthInterfaceMemSet = false;
    if (!userAuthInterfaceData.ReadBool(userAuthInterfaceMemSet)) {
        HDF_LOGE("%{public}s: failed to read userAuthInterfaceMemSet", __func__);
        return HDF_ERR_INVALID_PARAM;
    }
    uint64_t contextId = 0;
    if (!userAuthInterfaceData.ReadUint64(contextId)) {
        HDF_LOGE("%{public}s: read contextId failed!", __func__);
        return HDF_ERR_INVALID_PARAM;
    }

    OHOS::HDI::UserAuth::V4_1::AuthParamExt param;
    if (!AuthParamExtBlockUnmarshalling(userAuthInterfaceData, param)) {
        HDF_LOGE("%{public}s: read param failed!", __func__);
        return HDF_ERR_INVALID_PARAM;
    }

    std::vector<OHOS::HDI::UserAuth::V4_0::ScheduleInfo> scheduleInfos;
    if (userAuthInterfaceMemSet) {
        uint32_t capacity = 0;
        if (!userAuthInterfaceData.ReadUint32(capacity)) {
            HDF_LOGE("%{public}s: failed to read capacity", __func__);
            return HDF_ERR_INVALID_PARAM;
        }
        HDI_CHECK_VALUE_RETURN(capacity, >, HDI_BUFF_MAX_SIZE / sizeof(OHOS::HDI::UserAuth::V4_0::ScheduleInfo), HDF_ERR_INVALID_PARAM);
        scheduleInfos.reserve(capacity);
    }

    if (impl == nullptr) {
        HDF_LOGE("%{public}s: impl is nullptr!", __func__);
        return HDF_ERR_INVALID_PARAM;
    }

    int32_t userAuthInterfaceRet = impl->BeginAuthenticationExt(contextId, param, scheduleInfos);
    if (userAuthInterfaceRet != HDF_SUCCESS) {
        HDF_LOGE("%{public}s failed, error code is %{public}d", __func__, userAuthInterfaceRet);
        return userAuthInterfaceRet;
    }

    if (!userAuthInterfaceReply.WriteUint32(scheduleInfos.size())) {
        HDF_LOGE("%{public}s: write scheduleInfos size failed!", __func__);
        return HDF_ERR_INVALID_PARAM;
    }
    for (const auto& it0 : scheduleInfos) {
        if (!OHOS::HDI::UserAuth::V4_0::ScheduleInfoBlockMarshalling(userAuthInterfaceReply, it0)) {
            HDF_LOGE("%{public}s: write it0 failed!", __func__);
            return HDF_ERR_INVALID_PARAM;
        }
    }

    return userAuthInterfaceRet;
}

int32_t OHOS::HDI::UserAuth::V4_1::UserAuthInterfaceStub::UserAuthInterfaceStubBeginEnrollmentExt_(MessageParcel& userAuthInterfaceData, MessageParcel& userAuthInterfaceReply, MessageOption& userAuthInterfaceOption, sptr<OHOS::HDI::UserAuth::V4_1::IUserAuthInterface> impl)
{
    if (userAuthInterfaceData.ReadInterfaceToken() != OHOS::HDI::UserAuth::V4_1::IUserAuthInterface::GetDescriptor()) {
        HDF_LOGE("%{public}s: interface token check failed!", __func__);
        return HDF_ERR_INVALID_PARAM;
    }

    std::vector<uint8_t> authToken;
    if (!ReadPodArray(userAuthInterfaceData, authToken)) {
        HDF_LOGE("%{public}s: failed to read authToken", __func__);
        return HDF_ERR_INVALID_PARAM;
    }

    OHOS::HDI::UserAuth::V4_1::EnrollParamExt param;
    if (!EnrollParamExtBlockUnmarshalling(userAuthInterfaceData, param)) {
        HDF_LOGE("%{public}s: read param failed!", __func__);
        return HDF_ERR_INVALID_PARAM;
    }

    OHOS::HDI::UserAuth::V4_0::ScheduleInfo info;

    if (impl == nullptr) {
        HDF_LOGE("%{public}s: impl is nullptr!", __func__);
        return HDF_ERR_INVALID_PARAM;
    }

    int32_t userAuthInterfaceRet = impl->BeginEnrollmentExt(authToken, param, info);
    if (userAuthInterfaceRet != HDF_SUCCESS) {
        HDF_LOGE("%{public}s failed, error code is %{public}d", __func__, userAuthInterfaceRet);
        return userAuthInterfaceRet;
    }

    if (!OHOS::HDI::UserAuth::V4_0::ScheduleInfoBlockMarshalling(userAuthInterfaceReply, info)) {
        HDF_LOGE("%{public}s: write info failed!", __func__);
        return HDF_ERR_INVALID_PARAM;
    }

    return userAuthInterfaceRet;
}
} // V4_1
} // UserAuth
} // HDI
} // OHOS
