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

#ifndef OHOS_HDI_USER_AUTH_V4_0_USERAUTHINTERFACESERVICE_H
#define OHOS_HDI_USER_AUTH_V4_0_USERAUTHINTERFACESERVICE_H

#include "v4_0/iuser_auth_interface.h"

namespace OHOS {
namespace HDI {
namespace UserAuth {
namespace V4_0 {
class UserAuthInterfaceService : public OHOS::HDI::UserAuth::V4_0::IUserAuthInterface {
public:
    UserAuthInterfaceService() = default;
    virtual ~UserAuthInterfaceService() = default;

    int32_t Init(const std::string& deviceUdid) override;

    int32_t AddExecutor(const OHOS::HDI::UserAuth::V4_0::ExecutorRegisterInfo& info, uint64_t& index,
         std::vector<uint8_t>& publicKey, std::vector<uint64_t>& templateIds) override;

    int32_t DeleteExecutor(uint64_t index) override;

    int32_t OpenSession(int32_t userId, std::vector<uint8_t>& challenge) override;

    int32_t CloseSession(int32_t userId) override;

    int32_t UpdateEnrollmentResult(int32_t userId, const std::vector<uint8_t>& scheduleResult,
         OHOS::HDI::UserAuth::V4_0::EnrollResultInfo& info) override;

    int32_t CancelEnrollment(int32_t userId) override;

    int32_t DeleteCredential(int32_t userId, uint64_t credentialId, const std::vector<uint8_t>& authToken,
         OHOS::HDI::UserAuth::V4_0::CredentialOperateResult& operateResult) override;

    int32_t GetCredential(int32_t userId, int32_t authType,
         std::vector<OHOS::HDI::UserAuth::V4_0::CredentialInfo>& infos) override;

    int32_t GetUserInfo(int32_t userId, uint64_t& secureUid, int32_t& pinSubType,
         std::vector<OHOS::HDI::UserAuth::V4_0::EnrolledInfo>& infos) override;

    int32_t DeleteUser(int32_t userId, const std::vector<uint8_t>& authToken,
         std::vector<OHOS::HDI::UserAuth::V4_0::CredentialInfo>& deletedInfos, std::vector<uint8_t>& rootSecret) override;

    int32_t EnforceDeleteUser(int32_t userId,
         std::vector<OHOS::HDI::UserAuth::V4_0::CredentialInfo>& deletedInfos) override;

    int32_t UpdateAuthenticationResult(uint64_t contextId, const std::vector<uint8_t>& scheduleResult,
         OHOS::HDI::UserAuth::V4_0::AuthResultInfo& info, OHOS::HDI::UserAuth::V4_0::EnrolledState& enrolledState) override;

    int32_t CancelAuthentication(uint64_t contextId) override;

    int32_t UpdateIdentificationResult(uint64_t contextId, const std::vector<uint8_t>& scheduleResult,
         OHOS::HDI::UserAuth::V4_0::IdentifyResultInfo& info) override;

    int32_t CancelIdentification(uint64_t contextId) override;

    int32_t GetAvailableStatus(int32_t userId, int32_t authType, uint32_t authTrustLevel,
         int32_t& checkResult) override;

    int32_t GetValidSolution(int32_t userId, const std::vector<int32_t>& authTypes, uint32_t authTrustLevel,
         std::vector<int32_t>& validTypes) override;

    int32_t BeginAuthentication(uint64_t contextId, const OHOS::HDI::UserAuth::V4_0::AuthParam& param,
         std::vector<OHOS::HDI::UserAuth::V4_0::ScheduleInfo>& scheduleInfos) override;

    int32_t BeginEnrollment(const std::vector<uint8_t>& authToken, const OHOS::HDI::UserAuth::V4_0::EnrollParam& param,
         OHOS::HDI::UserAuth::V4_0::ScheduleInfo& info) override;

    int32_t BeginIdentification(uint64_t contextId, int32_t authType, const std::vector<uint8_t>& challenge,
         uint32_t executorSensorHint, OHOS::HDI::UserAuth::V4_0::ScheduleInfo& scheduleInfo) override;

    int32_t GetAllUserInfo(std::vector<OHOS::HDI::UserAuth::V4_0::UserInfo>& userInfos) override;

    int32_t GetAllExtUserInfo(std::vector<OHOS::HDI::UserAuth::V4_0::ExtUserInfo>& userInfos) override;

    int32_t GetEnrolledState(int32_t userId, int32_t authType,
         OHOS::HDI::UserAuth::V4_0::EnrolledState& enrolledState) override;

    int32_t CheckReuseUnlockResult(const OHOS::HDI::UserAuth::V4_0::ReuseUnlockParam& reuseParam,
         OHOS::HDI::UserAuth::V4_0::ReuseUnlockInfo& reuseInfo) override;

    int32_t SendMessage(uint64_t scheduleId, int32_t srcRole, const std::vector<uint8_t>& msg) override;

    int32_t RegisterMessageCallback(const sptr<OHOS::HDI::UserAuth::V4_0::IMessageCallback>& messageCallback) override;

    int32_t PrepareRemoteAuth(const std::string& remoteUdid) override;

    int32_t GetLocalScheduleFromMessage(const std::string& remoteUdid, const std::vector<uint8_t>& message,
         OHOS::HDI::UserAuth::V4_0::ScheduleInfo& scheduleInfo) override;

    int32_t GetSignedExecutorInfo(const std::vector<int32_t>& authTypes, int32_t executorRole,
         const std::string& remoteUdid, std::vector<uint8_t>& signedExecutorInfo) override;

    int32_t GetAuthResultFromMessage(const std::string& remoteUdid, const std::vector<uint8_t>& message,
         OHOS::HDI::UserAuth::V4_0::AuthResultInfo& authResultInfo) override;

    int32_t SetGlobalConfigParam(const OHOS::HDI::UserAuth::V4_0::GlobalConfigParam& param) override;

    int32_t GetCredentialById(uint64_t credentialId, OHOS::HDI::UserAuth::V4_0::CredentialInfo& info) override;

    int32_t VerifyAuthToken(const std::vector<uint8_t>& tokenIn, uint64_t allowableDuration,
         OHOS::HDI::UserAuth::V4_0::UserAuthTokenPlain& tokenPlainOut, std::vector<uint8_t>& rootSecret) override;

    int32_t UpdateAbandonResult(int32_t userId, const std::vector<uint8_t>& scheduleResult,
         std::vector<OHOS::HDI::UserAuth::V4_0::CredentialInfo>& infos) override;

    int32_t ClearUnavailableCredential(const std::vector<int32_t>& userIds,
         std::vector<OHOS::HDI::UserAuth::V4_0::CredentialInfo>& infos) override;

};
} // V4_0
} // UserAuth
} // HDI
} // OHOS

#endif // OHOS_HDI_USER_AUTH_V4_0_USERAUTHINTERFACESERVICE_H