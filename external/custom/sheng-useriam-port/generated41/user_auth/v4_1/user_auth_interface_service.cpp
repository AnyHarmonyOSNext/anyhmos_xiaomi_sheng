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

#include "v4_1/user_auth_interface_service.h"
#include <hdf_base.h>

#define HDF_LOG_TAG    user_auth_interface_service

namespace OHOS {
namespace HDI {
namespace UserAuth {
namespace V4_1 {
extern "C" IUserAuthInterface *UserAuthInterfaceImplGetInstance(void)
{
    return new (std::nothrow) UserAuthInterfaceService();
}

int32_t UserAuthInterfaceService::BeginAuthenticationExt(uint64_t contextId,
     const OHOS::HDI::UserAuth::V4_1::AuthParamExt& param, std::vector<OHOS::HDI::UserAuth::V4_0::ScheduleInfo>& scheduleInfos)
{
    return HDF_SUCCESS;
}

int32_t UserAuthInterfaceService::BeginEnrollmentExt(const std::vector<uint8_t>& authToken,
     const OHOS::HDI::UserAuth::V4_1::EnrollParamExt& param, OHOS::HDI::UserAuth::V4_0::ScheduleInfo& info)
{
    return HDF_SUCCESS;
}

int32_t UserAuthInterfaceService::Init(const std::string& deviceUdid)
{
    return HDF_SUCCESS;
}

int32_t UserAuthInterfaceService::AddExecutor(const OHOS::HDI::UserAuth::V4_0::ExecutorRegisterInfo& info,
     uint64_t& index, std::vector<uint8_t>& publicKey, std::vector<uint64_t>& templateIds)
{
    return HDF_SUCCESS;
}

int32_t UserAuthInterfaceService::DeleteExecutor(uint64_t index)
{
    return HDF_SUCCESS;
}

int32_t UserAuthInterfaceService::OpenSession(int32_t userId, std::vector<uint8_t>& challenge)
{
    return HDF_SUCCESS;
}

int32_t UserAuthInterfaceService::CloseSession(int32_t userId)
{
    return HDF_SUCCESS;
}

int32_t UserAuthInterfaceService::UpdateEnrollmentResult(int32_t userId, const std::vector<uint8_t>& scheduleResult,
     OHOS::HDI::UserAuth::V4_0::EnrollResultInfo& info)
{
    return HDF_SUCCESS;
}

int32_t UserAuthInterfaceService::CancelEnrollment(int32_t userId)
{
    return HDF_SUCCESS;
}

int32_t UserAuthInterfaceService::DeleteCredential(int32_t userId, uint64_t credentialId,
     const std::vector<uint8_t>& authToken, OHOS::HDI::UserAuth::V4_0::CredentialOperateResult& operateResult)
{
    return HDF_SUCCESS;
}

int32_t UserAuthInterfaceService::GetCredential(int32_t userId, int32_t authType,
     std::vector<OHOS::HDI::UserAuth::V4_0::CredentialInfo>& infos)
{
    return HDF_SUCCESS;
}

int32_t UserAuthInterfaceService::GetUserInfo(int32_t userId, uint64_t& secureUid, int32_t& pinSubType,
     std::vector<OHOS::HDI::UserAuth::V4_0::EnrolledInfo>& infos)
{
    return HDF_SUCCESS;
}

int32_t UserAuthInterfaceService::DeleteUser(int32_t userId, const std::vector<uint8_t>& authToken,
     std::vector<OHOS::HDI::UserAuth::V4_0::CredentialInfo>& deletedInfos, std::vector<uint8_t>& rootSecret)
{
    return HDF_SUCCESS;
}

int32_t UserAuthInterfaceService::EnforceDeleteUser(int32_t userId,
     std::vector<OHOS::HDI::UserAuth::V4_0::CredentialInfo>& deletedInfos)
{
    return HDF_SUCCESS;
}

int32_t UserAuthInterfaceService::UpdateAuthenticationResult(uint64_t contextId,
     const std::vector<uint8_t>& scheduleResult, OHOS::HDI::UserAuth::V4_0::AuthResultInfo& info, OHOS::HDI::UserAuth::V4_0::EnrolledState& enrolledState)
{
    return HDF_SUCCESS;
}

int32_t UserAuthInterfaceService::CancelAuthentication(uint64_t contextId)
{
    return HDF_SUCCESS;
}

int32_t UserAuthInterfaceService::UpdateIdentificationResult(uint64_t contextId,
     const std::vector<uint8_t>& scheduleResult, OHOS::HDI::UserAuth::V4_0::IdentifyResultInfo& info)
{
    return HDF_SUCCESS;
}

int32_t UserAuthInterfaceService::CancelIdentification(uint64_t contextId)
{
    return HDF_SUCCESS;
}

int32_t UserAuthInterfaceService::GetAvailableStatus(int32_t userId, int32_t authType, uint32_t authTrustLevel,
     int32_t& checkResult)
{
    return HDF_SUCCESS;
}

int32_t UserAuthInterfaceService::GetValidSolution(int32_t userId, const std::vector<int32_t>& authTypes,
     uint32_t authTrustLevel, std::vector<int32_t>& validTypes)
{
    return HDF_SUCCESS;
}

int32_t UserAuthInterfaceService::BeginAuthentication(uint64_t contextId,
     const OHOS::HDI::UserAuth::V4_0::AuthParam& param, std::vector<OHOS::HDI::UserAuth::V4_0::ScheduleInfo>& scheduleInfos)
{
    return HDF_SUCCESS;
}

int32_t UserAuthInterfaceService::BeginEnrollment(const std::vector<uint8_t>& authToken,
     const OHOS::HDI::UserAuth::V4_0::EnrollParam& param, OHOS::HDI::UserAuth::V4_0::ScheduleInfo& info)
{
    return HDF_SUCCESS;
}

int32_t UserAuthInterfaceService::BeginIdentification(uint64_t contextId, int32_t authType,
     const std::vector<uint8_t>& challenge, uint32_t executorSensorHint, OHOS::HDI::UserAuth::V4_0::ScheduleInfo& scheduleInfo)
{
    return HDF_SUCCESS;
}

int32_t UserAuthInterfaceService::GetAllUserInfo(std::vector<OHOS::HDI::UserAuth::V4_0::UserInfo>& userInfos)
{
    return HDF_SUCCESS;
}

int32_t UserAuthInterfaceService::GetAllExtUserInfo(std::vector<OHOS::HDI::UserAuth::V4_0::ExtUserInfo>& userInfos)
{
    return HDF_SUCCESS;
}

int32_t UserAuthInterfaceService::GetEnrolledState(int32_t userId, int32_t authType,
     OHOS::HDI::UserAuth::V4_0::EnrolledState& enrolledState)
{
    return HDF_SUCCESS;
}

int32_t UserAuthInterfaceService::CheckReuseUnlockResult(const OHOS::HDI::UserAuth::V4_0::ReuseUnlockParam& reuseParam,
     OHOS::HDI::UserAuth::V4_0::ReuseUnlockInfo& reuseInfo)
{
    return HDF_SUCCESS;
}

int32_t UserAuthInterfaceService::SendMessage(uint64_t scheduleId, int32_t srcRole, const std::vector<uint8_t>& msg)
{
    return HDF_SUCCESS;
}

int32_t UserAuthInterfaceService::RegisterMessageCallback(const sptr<OHOS::HDI::UserAuth::V4_0::IMessageCallback>& messageCallback)
{
    return HDF_SUCCESS;
}

int32_t UserAuthInterfaceService::PrepareRemoteAuth(const std::string& remoteUdid)
{
    return HDF_SUCCESS;
}

int32_t UserAuthInterfaceService::GetLocalScheduleFromMessage(const std::string& remoteUdid,
     const std::vector<uint8_t>& message, OHOS::HDI::UserAuth::V4_0::ScheduleInfo& scheduleInfo)
{
    return HDF_SUCCESS;
}

int32_t UserAuthInterfaceService::GetSignedExecutorInfo(const std::vector<int32_t>& authTypes, int32_t executorRole,
     const std::string& remoteUdid, std::vector<uint8_t>& signedExecutorInfo)
{
    return HDF_SUCCESS;
}

int32_t UserAuthInterfaceService::GetAuthResultFromMessage(const std::string& remoteUdid,
     const std::vector<uint8_t>& message, OHOS::HDI::UserAuth::V4_0::AuthResultInfo& authResultInfo)
{
    return HDF_SUCCESS;
}

int32_t UserAuthInterfaceService::SetGlobalConfigParam(const OHOS::HDI::UserAuth::V4_0::GlobalConfigParam& param)
{
    return HDF_SUCCESS;
}

int32_t UserAuthInterfaceService::GetCredentialById(uint64_t credentialId,
     OHOS::HDI::UserAuth::V4_0::CredentialInfo& info)
{
    return HDF_SUCCESS;
}

int32_t UserAuthInterfaceService::VerifyAuthToken(const std::vector<uint8_t>& tokenIn, uint64_t allowableDuration,
     OHOS::HDI::UserAuth::V4_0::UserAuthTokenPlain& tokenPlainOut, std::vector<uint8_t>& rootSecret)
{
    return HDF_SUCCESS;
}

int32_t UserAuthInterfaceService::UpdateAbandonResult(int32_t userId, const std::vector<uint8_t>& scheduleResult,
     std::vector<OHOS::HDI::UserAuth::V4_0::CredentialInfo>& infos)
{
    return HDF_SUCCESS;
}

int32_t UserAuthInterfaceService::ClearUnavailableCredential(const std::vector<int32_t>& userIds,
     std::vector<OHOS::HDI::UserAuth::V4_0::CredentialInfo>& infos)
{
    return HDF_SUCCESS;
}

} // V4_1
} // UserAuth
} // HDI
} // OHOS
