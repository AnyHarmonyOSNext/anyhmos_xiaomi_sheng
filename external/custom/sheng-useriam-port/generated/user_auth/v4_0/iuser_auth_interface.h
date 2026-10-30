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

#ifndef OHOS_HDI_USER_AUTH_V4_0_IUSERAUTHINTERFACE_H
#define OHOS_HDI_USER_AUTH_V4_0_IUSERAUTHINTERFACE_H

#include <stdint.h>
#include <string>
#include <vector>
#include <hdf_base.h>
#include <hdi_base.h>
#include "user_auth/v4_0/imessage_callback.h"
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
namespace HDI {
namespace UserAuth {
namespace V4_0 {
using namespace OHOS;
using namespace OHOS::HDI;

enum {
    CMD_USER_AUTH_INTERFACE_GET_VERSION = 0,
    CMD_USER_AUTH_INTERFACE_INIT = 1,
    CMD_USER_AUTH_INTERFACE_ADD_EXECUTOR = 2,
    CMD_USER_AUTH_INTERFACE_DELETE_EXECUTOR = 3,
    CMD_USER_AUTH_INTERFACE_OPEN_SESSION = 4,
    CMD_USER_AUTH_INTERFACE_CLOSE_SESSION = 5,
    CMD_USER_AUTH_INTERFACE_UPDATE_ENROLLMENT_RESULT = 6,
    CMD_USER_AUTH_INTERFACE_CANCEL_ENROLLMENT = 7,
    CMD_USER_AUTH_INTERFACE_DELETE_CREDENTIAL = 8,
    CMD_USER_AUTH_INTERFACE_GET_CREDENTIAL = 9,
    CMD_USER_AUTH_INTERFACE_GET_USER_INFO = 10,
    CMD_USER_AUTH_INTERFACE_DELETE_USER = 11,
    CMD_USER_AUTH_INTERFACE_ENFORCE_DELETE_USER = 12,
    CMD_USER_AUTH_INTERFACE_UPDATE_AUTHENTICATION_RESULT = 13,
    CMD_USER_AUTH_INTERFACE_CANCEL_AUTHENTICATION = 14,
    CMD_USER_AUTH_INTERFACE_UPDATE_IDENTIFICATION_RESULT = 15,
    CMD_USER_AUTH_INTERFACE_CANCEL_IDENTIFICATION = 16,
    CMD_USER_AUTH_INTERFACE_GET_AVAILABLE_STATUS = 17,
    CMD_USER_AUTH_INTERFACE_GET_VALID_SOLUTION = 18,
    CMD_USER_AUTH_INTERFACE_BEGIN_AUTHENTICATION = 19,
    CMD_USER_AUTH_INTERFACE_BEGIN_ENROLLMENT = 20,
    CMD_USER_AUTH_INTERFACE_BEGIN_IDENTIFICATION = 21,
    CMD_USER_AUTH_INTERFACE_GET_ALL_USER_INFO = 22,
    CMD_USER_AUTH_INTERFACE_GET_ALL_EXT_USER_INFO = 23,
    CMD_USER_AUTH_INTERFACE_GET_ENROLLED_STATE = 24,
    CMD_USER_AUTH_INTERFACE_CHECK_REUSE_UNLOCK_RESULT = 25,
    CMD_USER_AUTH_INTERFACE_SEND_MESSAGE = 26,
    CMD_USER_AUTH_INTERFACE_REGISTER_MESSAGE_CALLBACK = 27,
    CMD_USER_AUTH_INTERFACE_PREPARE_REMOTE_AUTH = 28,
    CMD_USER_AUTH_INTERFACE_GET_LOCAL_SCHEDULE_FROM_MESSAGE = 29,
    CMD_USER_AUTH_INTERFACE_GET_SIGNED_EXECUTOR_INFO = 30,
    CMD_USER_AUTH_INTERFACE_GET_AUTH_RESULT_FROM_MESSAGE = 31,
    CMD_USER_AUTH_INTERFACE_SET_GLOBAL_CONFIG_PARAM = 32,
    CMD_USER_AUTH_INTERFACE_GET_CREDENTIAL_BY_ID = 33,
    CMD_USER_AUTH_INTERFACE_VERIFY_AUTH_TOKEN = 34,
    CMD_USER_AUTH_INTERFACE_UPDATE_ABANDON_RESULT = 35,
    CMD_USER_AUTH_INTERFACE_CLEAR_UNAVAILABLE_CREDENTIAL = 36,
};

class IUserAuthInterface : public HdiBase {
public:
    DECLARE_HDI_DESCRIPTOR(u"ohos.hdi.user_auth.v4_0.IUserAuthInterface");

    virtual ~IUserAuthInterface() = default;

    static sptr<OHOS::HDI::UserAuth::V4_0::IUserAuthInterface> Get(bool isStub = false);
    static sptr<OHOS::HDI::UserAuth::V4_0::IUserAuthInterface> Get(const std::string &serviceName, bool isStub = false);

    virtual int32_t Init(const std::string& deviceUdid) = 0;

    virtual int32_t AddExecutor(const OHOS::HDI::UserAuth::V4_0::ExecutorRegisterInfo& info, uint64_t& index,
         std::vector<uint8_t>& publicKey, std::vector<uint64_t>& templateIds) = 0;

    virtual int32_t DeleteExecutor(uint64_t index) = 0;

    virtual int32_t OpenSession(int32_t userId, std::vector<uint8_t>& challenge) = 0;

    virtual int32_t CloseSession(int32_t userId) = 0;

    virtual int32_t UpdateEnrollmentResult(int32_t userId, const std::vector<uint8_t>& scheduleResult,
         OHOS::HDI::UserAuth::V4_0::EnrollResultInfo& info) = 0;

    virtual int32_t CancelEnrollment(int32_t userId) = 0;

    virtual int32_t DeleteCredential(int32_t userId, uint64_t credentialId, const std::vector<uint8_t>& authToken,
         OHOS::HDI::UserAuth::V4_0::CredentialOperateResult& operateResult) = 0;

    virtual int32_t GetCredential(int32_t userId, int32_t authType,
         std::vector<OHOS::HDI::UserAuth::V4_0::CredentialInfo>& infos) = 0;

    virtual int32_t GetUserInfo(int32_t userId, uint64_t& secureUid, int32_t& pinSubType,
         std::vector<OHOS::HDI::UserAuth::V4_0::EnrolledInfo>& infos) = 0;

    virtual int32_t DeleteUser(int32_t userId, const std::vector<uint8_t>& authToken,
         std::vector<OHOS::HDI::UserAuth::V4_0::CredentialInfo>& deletedInfos, std::vector<uint8_t>& rootSecret) = 0;

    virtual int32_t EnforceDeleteUser(int32_t userId,
         std::vector<OHOS::HDI::UserAuth::V4_0::CredentialInfo>& deletedInfos) = 0;

    virtual int32_t UpdateAuthenticationResult(uint64_t contextId, const std::vector<uint8_t>& scheduleResult,
         OHOS::HDI::UserAuth::V4_0::AuthResultInfo& info, OHOS::HDI::UserAuth::V4_0::EnrolledState& enrolledState) = 0;

    virtual int32_t CancelAuthentication(uint64_t contextId) = 0;

    virtual int32_t UpdateIdentificationResult(uint64_t contextId, const std::vector<uint8_t>& scheduleResult,
         OHOS::HDI::UserAuth::V4_0::IdentifyResultInfo& info) = 0;

    virtual int32_t CancelIdentification(uint64_t contextId) = 0;

    virtual int32_t GetAvailableStatus(int32_t userId, int32_t authType, uint32_t authTrustLevel,
         int32_t& checkResult) = 0;

    virtual int32_t GetValidSolution(int32_t userId, const std::vector<int32_t>& authTypes, uint32_t authTrustLevel,
         std::vector<int32_t>& validTypes) = 0;

    virtual int32_t BeginAuthentication(uint64_t contextId, const OHOS::HDI::UserAuth::V4_0::AuthParam& param,
         std::vector<OHOS::HDI::UserAuth::V4_0::ScheduleInfo>& scheduleInfos) = 0;

    virtual int32_t BeginEnrollment(const std::vector<uint8_t>& authToken,
         const OHOS::HDI::UserAuth::V4_0::EnrollParam& param, OHOS::HDI::UserAuth::V4_0::ScheduleInfo& info) = 0;

    virtual int32_t BeginIdentification(uint64_t contextId, int32_t authType, const std::vector<uint8_t>& challenge,
         uint32_t executorSensorHint, OHOS::HDI::UserAuth::V4_0::ScheduleInfo& scheduleInfo) = 0;

    virtual int32_t GetAllUserInfo(std::vector<OHOS::HDI::UserAuth::V4_0::UserInfo>& userInfos) = 0;

    virtual int32_t GetAllExtUserInfo(std::vector<OHOS::HDI::UserAuth::V4_0::ExtUserInfo>& userInfos) = 0;

    virtual int32_t GetEnrolledState(int32_t userId, int32_t authType,
         OHOS::HDI::UserAuth::V4_0::EnrolledState& enrolledState) = 0;

    virtual int32_t CheckReuseUnlockResult(const OHOS::HDI::UserAuth::V4_0::ReuseUnlockParam& reuseParam,
         OHOS::HDI::UserAuth::V4_0::ReuseUnlockInfo& reuseInfo) = 0;

    virtual int32_t SendMessage(uint64_t scheduleId, int32_t srcRole, const std::vector<uint8_t>& msg) = 0;

    virtual int32_t RegisterMessageCallback(const sptr<OHOS::HDI::UserAuth::V4_0::IMessageCallback>& messageCallback) = 0;

    virtual int32_t PrepareRemoteAuth(const std::string& remoteUdid) = 0;

    virtual int32_t GetLocalScheduleFromMessage(const std::string& remoteUdid, const std::vector<uint8_t>& message,
         OHOS::HDI::UserAuth::V4_0::ScheduleInfo& scheduleInfo) = 0;

    virtual int32_t GetSignedExecutorInfo(const std::vector<int32_t>& authTypes, int32_t executorRole,
         const std::string& remoteUdid, std::vector<uint8_t>& signedExecutorInfo) = 0;

    virtual int32_t GetAuthResultFromMessage(const std::string& remoteUdid, const std::vector<uint8_t>& message,
         OHOS::HDI::UserAuth::V4_0::AuthResultInfo& authResultInfo) = 0;

    virtual int32_t SetGlobalConfigParam(const OHOS::HDI::UserAuth::V4_0::GlobalConfigParam& param) = 0;

    virtual int32_t GetCredentialById(uint64_t credentialId, OHOS::HDI::UserAuth::V4_0::CredentialInfo& info) = 0;

    virtual int32_t VerifyAuthToken(const std::vector<uint8_t>& tokenIn, uint64_t allowableDuration,
         OHOS::HDI::UserAuth::V4_0::UserAuthTokenPlain& tokenPlainOut, std::vector<uint8_t>& rootSecret) = 0;

    virtual int32_t UpdateAbandonResult(int32_t userId, const std::vector<uint8_t>& scheduleResult,
         std::vector<OHOS::HDI::UserAuth::V4_0::CredentialInfo>& infos) = 0;

    virtual int32_t ClearUnavailableCredential(const std::vector<int32_t>& userIds,
         std::vector<OHOS::HDI::UserAuth::V4_0::CredentialInfo>& infos) = 0;

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

#endif // OHOS_HDI_USER_AUTH_V4_0_IUSERAUTHINTERFACE_H