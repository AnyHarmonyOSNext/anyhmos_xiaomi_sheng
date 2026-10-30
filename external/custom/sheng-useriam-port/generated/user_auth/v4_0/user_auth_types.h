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

#ifndef OHOS_HDI_USER_AUTH_V4_0_USERAUTHTYPES_H
#define OHOS_HDI_USER_AUTH_V4_0_USERAUTHTYPES_H

#include <cstdbool>
#include <cstdint>
#include <string>
#include <vector>

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
namespace V4_0 {

using namespace OHOS;

enum AuthType : int32_t {
    ALL = 0,
    PIN = 1,
    FACE = 2,
    FINGERPRINT = 4,
    RECOVERY_KEY = 8,
    PRIVATE_PIN = 16,
};

enum ExecutorRole : int32_t {
    COLLECTOR = 1,
    VERIFIER = 2,
    ALL_IN_ONE = 3,
};

enum ExecutorSecureLevel : int32_t {
    ESL0 = 0,
    ESL1 = 1,
    ESL2 = 2,
    ESL3 = 3,
};

enum PinSubType : int32_t {
    PIN_SIX = 10000,
    PIN_NUMBER = 10001,
    PIN_MIX = 10002,
    PIN_FOUR = 10003,
    PATTERN = 10004,
    PIN_QUESTION = 10005,
};

enum ScheduleMode : int32_t {
    ENROLL = 0,
    AUTH = 1,
    IDENTIFY = 2,
    ABANDON = 4,
};

enum AuthIntent : int32_t {
    DEFUALT = 0,
    UNLOCK = 1,
    SILENT_AUTH = 2,
    QUESTION_AUTH = 3,
    ABANDONED_PIN_AUTH = 4,
};

enum UserType : int32_t {
    MAIN = 0,
    SUB = 1,
    PRIVATE = 2,
};

enum ReuseMode : int32_t {
    AUTH_TYPE_RELEVANT = 1,
    AUTH_TYPE_IRRELEVANT = 2,
    CALLER_IRRELEVANT_AUTH_TYPE_RELEVANT = 3,
    CALLER_IRRELEVANT_AUTH_TYPE_IRRELEVANT = 4,
};

struct ExecutorRegisterInfo {
    int32_t authType;
    int32_t executorRole;
    uint32_t executorSensorHint;
    uint32_t executorMatcher;
    int32_t esl;
    uint32_t maxTemplateAcl;
    std::vector<uint8_t> publicKey;
    std::string deviceUdid;
    std::vector<uint8_t> signedRemoteExecutorInfo;
};

struct ExecutorInfo {
    uint64_t executorIndex;
    OHOS::HDI::UserAuth::V4_0::ExecutorRegisterInfo info;
};

struct ExecutorSendMsg {
    uint64_t executorIndex;
    int32_t commandId;
    std::vector<uint8_t> msg;
};

struct AuthResultInfo {
    int32_t result;
    int32_t lockoutDuration;
    int32_t remainAttempts;
    std::vector<OHOS::HDI::UserAuth::V4_0::ExecutorSendMsg> msgs;
    std::vector<uint8_t> token;
    std::vector<uint8_t> rootSecret;
    int32_t userId;
    uint64_t credentialId;
    int64_t pinExpiredInfo;
    std::vector<uint8_t> remoteAuthResultMsg;
    bool reEnrollFlag;
};

struct IdentifyResultInfo {
    int32_t result;
    int32_t userId;
    std::vector<uint8_t> token;
};

struct CredentialInfo {
    uint64_t credentialId;
    uint64_t executorIndex;
    uint64_t templateId;
    int32_t authType;
    uint32_t executorMatcher;
    uint32_t executorSensorHint;
    int32_t authSubType;
    bool isAbandoned;
    int64_t validityPeriod;
} __attribute__ ((aligned(8)));

struct EnrolledInfo {
    uint64_t enrolledId;
    int32_t authType;
} __attribute__ ((aligned(8)));

struct EnrollResultInfo {
    uint64_t credentialId;
    OHOS::HDI::UserAuth::V4_0::CredentialInfo oldInfo;
    std::vector<uint8_t> rootSecret;
    std::vector<uint8_t> oldRootSecret;
    std::vector<uint8_t> authToken;
};

struct ScheduleInfo {
    uint64_t scheduleId;
    std::vector<uint64_t> templateIds;
    int32_t authType;
    uint32_t executorMatcher;
    int32_t scheduleMode;
    std::vector<uint64_t> executorIndexes;
    std::vector<std::vector<uint8_t>> executorMessages;
};

struct UserInfo {
    uint64_t secureUid;
    int32_t pinSubType;
    std::vector<OHOS::HDI::UserAuth::V4_0::EnrolledInfo> enrolledInfos;
};

struct ExtUserInfo {
    int32_t userId;
    OHOS::HDI::UserAuth::V4_0::UserInfo userInfo;
};

struct AuthParamBase {
    int32_t userId;
    uint32_t authTrustLevel;
    uint32_t executorSensorHint;
    std::vector<uint8_t> challenge;
    std::string callerName;
    int32_t callerType;
    int32_t apiVersion;
};

struct AuthParam {
    OHOS::HDI::UserAuth::V4_0::AuthParamBase baseParam;
    int32_t authType;
    int32_t authIntent;
    bool isOsAccountVerified;
    std::string collectorUdid;
};

struct ReuseUnlockParam {
    OHOS::HDI::UserAuth::V4_0::AuthParamBase baseParam;
    std::vector<int32_t> authTypes;
    uint64_t reuseUnlockResultDuration;
    int32_t reuseUnlockResultMode;
};

struct EnrollParam {
    int32_t authType;
    uint32_t executorSensorHint;
    std::string callerName;
    int32_t callerType;
    int32_t apiVersion;
    int32_t userId;
    int32_t userType;
    int32_t authSubType;
};

struct EnrolledState {
    uint64_t credentialDigest;
    uint16_t credentialCount;
} __attribute__ ((aligned(8)));

struct ReuseUnlockInfo {
    int32_t authType;
    std::vector<uint8_t> token;
    OHOS::HDI::UserAuth::V4_0::EnrolledState enrolledState;
};

enum GlobalConfigType : int32_t {
    PIN_EXPIRED_PERIOD = 1,
    ENABLE_STATUS = 2,
};

union GlobalConfigValue {
    int64_t pinExpiredPeriod;
    bool enableStatus;
}  __attribute__ ((aligned(8)));

struct GlobalConfigParam {
    int32_t type;
    OHOS::HDI::UserAuth::V4_0::GlobalConfigValue value;
    std::vector<int32_t> userIds;
    std::vector<int32_t> authTypes;
};

struct UserAuthTokenPlain {
    uint32_t version;
    int32_t userId;
    std::vector<uint8_t> challenge;
    uint64_t timeInterval;
    uint32_t authTrustLevel;
    int32_t authType;
    int32_t authMode;
    uint32_t securityLevel;
    int32_t tokenType;
    uint64_t secureUid;
    uint64_t enrolledId;
    uint64_t credentialId;
    std::string collectorUdid;
    std::string verifierUdid;
};

enum CredentialOperateType : int32_t {
    CREDENTIAL_DELETE = 1,
    CREDENTIAL_ABANDON = 2,
};

struct CredentialOperateResult {
    OHOS::HDI::UserAuth::V4_0::CredentialOperateType operateType;
    OHOS::HDI::UserAuth::V4_0::ScheduleInfo scheduleInfo;
    std::vector<OHOS::HDI::UserAuth::V4_0::CredentialInfo> credentialInfos;
};

bool ExecutorRegisterInfoBlockMarshalling(OHOS::MessageParcel &data, const OHOS::HDI::UserAuth::V4_0::ExecutorRegisterInfo& dataBlock);

bool ExecutorRegisterInfoBlockUnmarshalling(OHOS::MessageParcel &data, OHOS::HDI::UserAuth::V4_0::ExecutorRegisterInfo& dataBlock);

bool ExecutorInfoBlockMarshalling(OHOS::MessageParcel &data, const OHOS::HDI::UserAuth::V4_0::ExecutorInfo& dataBlock);

bool ExecutorInfoBlockUnmarshalling(OHOS::MessageParcel &data, OHOS::HDI::UserAuth::V4_0::ExecutorInfo& dataBlock);

bool ExecutorSendMsgBlockMarshalling(OHOS::MessageParcel &data, const OHOS::HDI::UserAuth::V4_0::ExecutorSendMsg& dataBlock);

bool ExecutorSendMsgBlockUnmarshalling(OHOS::MessageParcel &data, OHOS::HDI::UserAuth::V4_0::ExecutorSendMsg& dataBlock);

bool AuthResultInfoBlockMarshalling(OHOS::MessageParcel &data, const OHOS::HDI::UserAuth::V4_0::AuthResultInfo& dataBlock);

bool AuthResultInfoBlockUnmarshalling(OHOS::MessageParcel &data, OHOS::HDI::UserAuth::V4_0::AuthResultInfo& dataBlock);

bool IdentifyResultInfoBlockMarshalling(OHOS::MessageParcel &data, const OHOS::HDI::UserAuth::V4_0::IdentifyResultInfo& dataBlock);

bool IdentifyResultInfoBlockUnmarshalling(OHOS::MessageParcel &data, OHOS::HDI::UserAuth::V4_0::IdentifyResultInfo& dataBlock);

bool CredentialInfoBlockMarshalling(OHOS::MessageParcel &data, const OHOS::HDI::UserAuth::V4_0::CredentialInfo& dataBlock);

bool CredentialInfoBlockUnmarshalling(OHOS::MessageParcel &data, OHOS::HDI::UserAuth::V4_0::CredentialInfo& dataBlock);

bool EnrolledInfoBlockMarshalling(OHOS::MessageParcel &data, const OHOS::HDI::UserAuth::V4_0::EnrolledInfo& dataBlock);

bool EnrolledInfoBlockUnmarshalling(OHOS::MessageParcel &data, OHOS::HDI::UserAuth::V4_0::EnrolledInfo& dataBlock);

bool EnrollResultInfoBlockMarshalling(OHOS::MessageParcel &data, const OHOS::HDI::UserAuth::V4_0::EnrollResultInfo& dataBlock);

bool EnrollResultInfoBlockUnmarshalling(OHOS::MessageParcel &data, OHOS::HDI::UserAuth::V4_0::EnrollResultInfo& dataBlock);

bool ScheduleInfoBlockMarshalling(OHOS::MessageParcel &data, const OHOS::HDI::UserAuth::V4_0::ScheduleInfo& dataBlock);

bool ScheduleInfoBlockUnmarshalling(OHOS::MessageParcel &data, OHOS::HDI::UserAuth::V4_0::ScheduleInfo& dataBlock);

bool UserInfoBlockMarshalling(OHOS::MessageParcel &data, const OHOS::HDI::UserAuth::V4_0::UserInfo& dataBlock);

bool UserInfoBlockUnmarshalling(OHOS::MessageParcel &data, OHOS::HDI::UserAuth::V4_0::UserInfo& dataBlock);

bool ExtUserInfoBlockMarshalling(OHOS::MessageParcel &data, const OHOS::HDI::UserAuth::V4_0::ExtUserInfo& dataBlock);

bool ExtUserInfoBlockUnmarshalling(OHOS::MessageParcel &data, OHOS::HDI::UserAuth::V4_0::ExtUserInfo& dataBlock);

bool AuthParamBaseBlockMarshalling(OHOS::MessageParcel &data, const OHOS::HDI::UserAuth::V4_0::AuthParamBase& dataBlock);

bool AuthParamBaseBlockUnmarshalling(OHOS::MessageParcel &data, OHOS::HDI::UserAuth::V4_0::AuthParamBase& dataBlock);

bool AuthParamBlockMarshalling(OHOS::MessageParcel &data, const OHOS::HDI::UserAuth::V4_0::AuthParam& dataBlock);

bool AuthParamBlockUnmarshalling(OHOS::MessageParcel &data, OHOS::HDI::UserAuth::V4_0::AuthParam& dataBlock);

bool ReuseUnlockParamBlockMarshalling(OHOS::MessageParcel &data, const OHOS::HDI::UserAuth::V4_0::ReuseUnlockParam& dataBlock);

bool ReuseUnlockParamBlockUnmarshalling(OHOS::MessageParcel &data, OHOS::HDI::UserAuth::V4_0::ReuseUnlockParam& dataBlock);

bool EnrollParamBlockMarshalling(OHOS::MessageParcel &data, const OHOS::HDI::UserAuth::V4_0::EnrollParam& dataBlock);

bool EnrollParamBlockUnmarshalling(OHOS::MessageParcel &data, OHOS::HDI::UserAuth::V4_0::EnrollParam& dataBlock);

bool EnrolledStateBlockMarshalling(OHOS::MessageParcel &data, const OHOS::HDI::UserAuth::V4_0::EnrolledState& dataBlock);

bool EnrolledStateBlockUnmarshalling(OHOS::MessageParcel &data, OHOS::HDI::UserAuth::V4_0::EnrolledState& dataBlock);

bool ReuseUnlockInfoBlockMarshalling(OHOS::MessageParcel &data, const OHOS::HDI::UserAuth::V4_0::ReuseUnlockInfo& dataBlock);

bool ReuseUnlockInfoBlockUnmarshalling(OHOS::MessageParcel &data, OHOS::HDI::UserAuth::V4_0::ReuseUnlockInfo& dataBlock);

bool GlobalConfigParamBlockMarshalling(OHOS::MessageParcel &data, const OHOS::HDI::UserAuth::V4_0::GlobalConfigParam& dataBlock);

bool GlobalConfigParamBlockUnmarshalling(OHOS::MessageParcel &data, OHOS::HDI::UserAuth::V4_0::GlobalConfigParam& dataBlock);

bool UserAuthTokenPlainBlockMarshalling(OHOS::MessageParcel &data, const OHOS::HDI::UserAuth::V4_0::UserAuthTokenPlain& dataBlock);

bool UserAuthTokenPlainBlockUnmarshalling(OHOS::MessageParcel &data, OHOS::HDI::UserAuth::V4_0::UserAuthTokenPlain& dataBlock);

bool CredentialOperateResultBlockMarshalling(OHOS::MessageParcel &data, const OHOS::HDI::UserAuth::V4_0::CredentialOperateResult& dataBlock);

bool CredentialOperateResultBlockUnmarshalling(OHOS::MessageParcel &data, OHOS::HDI::UserAuth::V4_0::CredentialOperateResult& dataBlock);

} // V4_0
} // UserAuth
} // HDI
} // OHOS

#endif // OHOS_HDI_USER_AUTH_V4_0_USERAUTHTYPES_H