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

#include "v4_1/user_auth_interface_proxy.h"
#include <hdf_base.h>
#include <hdf_core_log.h>
#include <hdi_support.h>
#include <iservmgr_hdi.h>
#include <message_option.h>
#include <message_parcel.h>
#include <string_ex.h>

#define HDF_LOG_TAG    user_auth_interface_proxy

namespace OHOS {
namespace HDI {
namespace UserAuth {
namespace V4_1 {

template<typename ElementType>
static bool WritePodArray(MessageParcel &parcel, const std::vector<ElementType> &data);

template<typename ChildType, typename ParentType>
static sptr<ChildType> CastFromTemplate(const sptr<ParentType> &parent)
{
    if (parent == nullptr) {
        HDF_LOGE("%{public}s:parent is nullptr!", __func__);
        return nullptr;
    }

    if (!parent->IsProxy()) {
        HDF_LOGE("%{public}s:not proxy, not support castfrom!", __func__);
        return nullptr;
    }

    sptr<IRemoteObject> remote = OHOS::HDI::hdi_objcast<ParentType>(parent);
    if (remote == nullptr) {
        HDF_LOGE("%{public}s:hdi_objcast failed!", __func__);
        return nullptr;
    }

    sptr<ChildType> proxy = OHOS::HDI::hdi_facecast<ChildType>(remote);
    if (proxy == nullptr) {
        HDF_LOGE("%{public}s:hdi_facecast failed!", __func__);
        return nullptr;
    }

    uint32_t serMajorVer = 0;
    uint32_t serMinorVer = 0;
    int32_t userAuthInterfaceRet = proxy->GetVersion(serMajorVer, serMinorVer);
    if (userAuthInterfaceRet != HDF_SUCCESS) {
        HDF_LOGE("%{public}s:get version failed!", __func__);
        return nullptr;
    }

    if (serMajorVer != 4) {
        HDF_LOGE("%{public}s:check version failed! version of service:%u.%u, version of client:4.1", __func__, serMajorVer, serMinorVer);
        return nullptr;
    }

    return proxy;
}

sptr<OHOS::HDI::UserAuth::V4_1::IUserAuthInterface> OHOS::HDI::UserAuth::V4_1::IUserAuthInterface::Get(bool isStub)
{
    return IUserAuthInterface::Get("user_auth_interface_service", isStub);
}

sptr<OHOS::HDI::UserAuth::V4_1::IUserAuthInterface> OHOS::HDI::UserAuth::V4_1::IUserAuthInterface::Get(const std::string& serviceName, bool isStub)
{
    if (isStub) {
        std::string desc = Str16ToStr8(OHOS::HDI::UserAuth::V4_1::IUserAuthInterface::GetDescriptor());
        void *impl = LoadHdiImpl(desc.c_str(), serviceName == "user_auth_interface_service" ? "service" : serviceName.c_str());
        if (impl == nullptr) {
            HDF_LOGE("failed to load hdi impl %{public}s", desc.data());
            return nullptr;
        }
        return reinterpret_cast<OHOS::HDI::UserAuth::V4_1::IUserAuthInterface *>(impl);
    }

    using namespace OHOS::HDI::ServiceManager::V1_0;
    auto servMgr = IServiceManager::Get();
    if (servMgr == nullptr) {
        HDF_LOGE("%{public}s:get IServiceManager failed!", __func__);
        return nullptr;
    }

    sptr<IRemoteObject> remote = servMgr->GetService(serviceName.c_str());
    if (remote == nullptr) {
        HDF_LOGE("%{public}s:get remote object failed!", __func__);
        return nullptr;
    }

    sptr<OHOS::HDI::UserAuth::V4_1::UserAuthInterfaceProxy> proxy = new OHOS::HDI::UserAuth::V4_1::UserAuthInterfaceProxy(remote);
    if (proxy == nullptr) {
        HDF_LOGE("%{public}s:iface_cast failed!", __func__);
        return nullptr;
    }

    proxy->servMgr_ = OHOS::HDI::hdi_objcast<IServiceManager>(servMgr);
    proxy->deathRecipient_ = new OHOS::HDI::UserAuth::V4_1::UserAuthInterfaceProxy::IServiceManagerDeathRecipient(proxy);
    proxy->servMgr_->AddDeathRecipient(proxy->deathRecipient_);
    proxy->isReconnected_ = false;
    proxy->serviceName_ = serviceName;
    uint32_t serMajorVer = 0;
    uint32_t serMinorVer = 0;
    int32_t userAuthInterfaceRet = proxy->GetVersion(serMajorVer, serMinorVer);
    if (userAuthInterfaceRet != HDF_SUCCESS) {
        HDF_LOGE("%{public}s:get version failed!", __func__);
        return nullptr;
    }

    if (serMajorVer != 4) {
        HDF_LOGE("%{public}s:check version failed! version of service:%u.%u, version of client:4.1", __func__, serMajorVer, serMinorVer);
        return nullptr;
    }

    return proxy;
}

int32_t OHOS::HDI::UserAuth::V4_1::UserAuthInterfaceProxy::Reconnect(
    sptr<OHOS::HDI::UserAuth::V4_1::UserAuthInterfaceProxy> proxy) 
{
    if (proxy == nullptr) {
        HDF_LOGW("Reconnect failed : input proxy is null");
        return HDF_FAILURE;
    }
    using namespace OHOS::HDI::ServiceManager::V1_0;
    proxy->isReconnected_ = false;
    auto iServMgr = IServiceManager::Get();
    if (iServMgr == nullptr) {
        HDF_LOGW("Reconnect failed : iServMgr is null");
        return HDF_FAILURE;
    };
    proxy->reconnectRemote_ = iServMgr->GetService(proxy->serviceName_.c_str());
    if (proxy->reconnectRemote_ == nullptr) {
        HDF_LOGW("Reconnect failed : reconnectRemote_ is null");
        return HDF_FAILURE;
    }
    proxy->servMgr_ = OHOS::HDI::hdi_objcast<IServiceManager>(iServMgr);
    if (proxy->servMgr_ == nullptr) {
        HDF_LOGE("%{public}s:get IServiceManager failed!", __func__);
        return HDF_FAILURE;
    }
    proxy->servMgr_->AddDeathRecipient(
        new OHOS::HDI::UserAuth::V4_1::UserAuthInterfaceProxy::IServiceManagerDeathRecipient(proxy));
    proxy->isReconnected_ = true;
    return HDF_SUCCESS;
}

sptr<OHOS::HDI::UserAuth::V4_1::IUserAuthInterface> OHOS::HDI::UserAuth::V4_1::IUserAuthInterface::CastFrom(const sptr<OHOS::HDI::UserAuth::V4_0::IUserAuthInterface> &parent)
{
    return CastFromTemplate<OHOS::HDI::UserAuth::V4_1::IUserAuthInterface, OHOS::HDI::UserAuth::V4_0::IUserAuthInterface>(parent);
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
int32_t OHOS::HDI::UserAuth::V4_1::UserAuthInterfaceProxy::BeginAuthenticationExt(uint64_t contextId,
     const OHOS::HDI::UserAuth::V4_1::AuthParamExt& param, std::vector<OHOS::HDI::UserAuth::V4_0::ScheduleInfo>& scheduleInfos)
{
    return OHOS::HDI::UserAuth::V4_1::UserAuthInterfaceProxy::BeginAuthenticationExt_(contextId, param, scheduleInfos, GetCurrentRemote());
}

int32_t OHOS::HDI::UserAuth::V4_1::UserAuthInterfaceProxy::BeginEnrollmentExt(const std::vector<uint8_t>& authToken,
     const OHOS::HDI::UserAuth::V4_1::EnrollParamExt& param, OHOS::HDI::UserAuth::V4_0::ScheduleInfo& info)
{
    return OHOS::HDI::UserAuth::V4_1::UserAuthInterfaceProxy::BeginEnrollmentExt_(authToken, param, info, GetCurrentRemote());
}

int32_t OHOS::HDI::UserAuth::V4_1::UserAuthInterfaceProxy::Init(const std::string& deviceUdid)
{
    return OHOS::HDI::UserAuth::V4_0::UserAuthInterfaceProxy::Init_(deviceUdid, GetCurrentRemote());
}

int32_t OHOS::HDI::UserAuth::V4_1::UserAuthInterfaceProxy::AddExecutor(const OHOS::HDI::UserAuth::V4_0::ExecutorRegisterInfo& info, uint64_t& index, std::vector<uint8_t>& publicKey, std::vector<uint64_t>& templateIds)
{
    return OHOS::HDI::UserAuth::V4_0::UserAuthInterfaceProxy::AddExecutor_(info, index, publicKey, templateIds, GetCurrentRemote());
}

int32_t OHOS::HDI::UserAuth::V4_1::UserAuthInterfaceProxy::DeleteExecutor(uint64_t index)
{
    return OHOS::HDI::UserAuth::V4_0::UserAuthInterfaceProxy::DeleteExecutor_(index, GetCurrentRemote());
}

int32_t OHOS::HDI::UserAuth::V4_1::UserAuthInterfaceProxy::OpenSession(int32_t userId, std::vector<uint8_t>& challenge)
{
    return OHOS::HDI::UserAuth::V4_0::UserAuthInterfaceProxy::OpenSession_(userId, challenge, GetCurrentRemote());
}

int32_t OHOS::HDI::UserAuth::V4_1::UserAuthInterfaceProxy::CloseSession(int32_t userId)
{
    return OHOS::HDI::UserAuth::V4_0::UserAuthInterfaceProxy::CloseSession_(userId, GetCurrentRemote());
}

int32_t OHOS::HDI::UserAuth::V4_1::UserAuthInterfaceProxy::UpdateEnrollmentResult(int32_t userId,
     const std::vector<uint8_t>& scheduleResult, OHOS::HDI::UserAuth::V4_0::EnrollResultInfo& info)
{
    return OHOS::HDI::UserAuth::V4_0::UserAuthInterfaceProxy::UpdateEnrollmentResult_(userId, scheduleResult, info, GetCurrentRemote());
}

int32_t OHOS::HDI::UserAuth::V4_1::UserAuthInterfaceProxy::CancelEnrollment(int32_t userId)
{
    return OHOS::HDI::UserAuth::V4_0::UserAuthInterfaceProxy::CancelEnrollment_(userId, GetCurrentRemote());
}

int32_t OHOS::HDI::UserAuth::V4_1::UserAuthInterfaceProxy::DeleteCredential(int32_t userId, uint64_t credentialId,
     const std::vector<uint8_t>& authToken, OHOS::HDI::UserAuth::V4_0::CredentialOperateResult& operateResult)
{
    return OHOS::HDI::UserAuth::V4_0::UserAuthInterfaceProxy::DeleteCredential_(userId, credentialId, authToken, operateResult, GetCurrentRemote());
}

int32_t OHOS::HDI::UserAuth::V4_1::UserAuthInterfaceProxy::GetCredential(int32_t userId, int32_t authType,
     std::vector<OHOS::HDI::UserAuth::V4_0::CredentialInfo>& infos)
{
    return OHOS::HDI::UserAuth::V4_0::UserAuthInterfaceProxy::GetCredential_(userId, authType, infos, GetCurrentRemote());
}

int32_t OHOS::HDI::UserAuth::V4_1::UserAuthInterfaceProxy::GetUserInfo(int32_t userId, uint64_t& secureUid,
     int32_t& pinSubType, std::vector<OHOS::HDI::UserAuth::V4_0::EnrolledInfo>& infos)
{
    return OHOS::HDI::UserAuth::V4_0::UserAuthInterfaceProxy::GetUserInfo_(userId, secureUid, pinSubType, infos, GetCurrentRemote());
}

int32_t OHOS::HDI::UserAuth::V4_1::UserAuthInterfaceProxy::DeleteUser(int32_t userId,
     const std::vector<uint8_t>& authToken, std::vector<OHOS::HDI::UserAuth::V4_0::CredentialInfo>& deletedInfos, std::vector<uint8_t>& rootSecret)
{
    return OHOS::HDI::UserAuth::V4_0::UserAuthInterfaceProxy::DeleteUser_(userId, authToken, deletedInfos, rootSecret, GetCurrentRemote());
}

int32_t OHOS::HDI::UserAuth::V4_1::UserAuthInterfaceProxy::EnforceDeleteUser(int32_t userId,
     std::vector<OHOS::HDI::UserAuth::V4_0::CredentialInfo>& deletedInfos)
{
    return OHOS::HDI::UserAuth::V4_0::UserAuthInterfaceProxy::EnforceDeleteUser_(userId, deletedInfos, GetCurrentRemote());
}

int32_t OHOS::HDI::UserAuth::V4_1::UserAuthInterfaceProxy::UpdateAuthenticationResult(uint64_t contextId,
     const std::vector<uint8_t>& scheduleResult, OHOS::HDI::UserAuth::V4_0::AuthResultInfo& info, OHOS::HDI::UserAuth::V4_0::EnrolledState& enrolledState)
{
    return OHOS::HDI::UserAuth::V4_0::UserAuthInterfaceProxy::UpdateAuthenticationResult_(contextId, scheduleResult, info, enrolledState, GetCurrentRemote());
}

int32_t OHOS::HDI::UserAuth::V4_1::UserAuthInterfaceProxy::CancelAuthentication(uint64_t contextId)
{
    return OHOS::HDI::UserAuth::V4_0::UserAuthInterfaceProxy::CancelAuthentication_(contextId, GetCurrentRemote());
}

int32_t OHOS::HDI::UserAuth::V4_1::UserAuthInterfaceProxy::UpdateIdentificationResult(uint64_t contextId,
     const std::vector<uint8_t>& scheduleResult, OHOS::HDI::UserAuth::V4_0::IdentifyResultInfo& info)
{
    return OHOS::HDI::UserAuth::V4_0::UserAuthInterfaceProxy::UpdateIdentificationResult_(contextId, scheduleResult, info, GetCurrentRemote());
}

int32_t OHOS::HDI::UserAuth::V4_1::UserAuthInterfaceProxy::CancelIdentification(uint64_t contextId)
{
    return OHOS::HDI::UserAuth::V4_0::UserAuthInterfaceProxy::CancelIdentification_(contextId, GetCurrentRemote());
}

int32_t OHOS::HDI::UserAuth::V4_1::UserAuthInterfaceProxy::GetAvailableStatus(int32_t userId, int32_t authType,
     uint32_t authTrustLevel, int32_t& checkResult)
{
    return OHOS::HDI::UserAuth::V4_0::UserAuthInterfaceProxy::GetAvailableStatus_(userId, authType, authTrustLevel, checkResult, GetCurrentRemote());
}

int32_t OHOS::HDI::UserAuth::V4_1::UserAuthInterfaceProxy::GetValidSolution(int32_t userId,
     const std::vector<int32_t>& authTypes, uint32_t authTrustLevel, std::vector<int32_t>& validTypes)
{
    return OHOS::HDI::UserAuth::V4_0::UserAuthInterfaceProxy::GetValidSolution_(userId, authTypes, authTrustLevel, validTypes, GetCurrentRemote());
}

int32_t OHOS::HDI::UserAuth::V4_1::UserAuthInterfaceProxy::BeginAuthentication(uint64_t contextId,
     const OHOS::HDI::UserAuth::V4_0::AuthParam& param, std::vector<OHOS::HDI::UserAuth::V4_0::ScheduleInfo>& scheduleInfos)
{
    return OHOS::HDI::UserAuth::V4_0::UserAuthInterfaceProxy::BeginAuthentication_(contextId, param, scheduleInfos, GetCurrentRemote());
}

int32_t OHOS::HDI::UserAuth::V4_1::UserAuthInterfaceProxy::BeginEnrollment(const std::vector<uint8_t>& authToken,
     const OHOS::HDI::UserAuth::V4_0::EnrollParam& param, OHOS::HDI::UserAuth::V4_0::ScheduleInfo& info)
{
    return OHOS::HDI::UserAuth::V4_0::UserAuthInterfaceProxy::BeginEnrollment_(authToken, param, info, GetCurrentRemote());
}

int32_t OHOS::HDI::UserAuth::V4_1::UserAuthInterfaceProxy::BeginIdentification(uint64_t contextId, int32_t authType,
     const std::vector<uint8_t>& challenge, uint32_t executorSensorHint, OHOS::HDI::UserAuth::V4_0::ScheduleInfo& scheduleInfo)
{
    return OHOS::HDI::UserAuth::V4_0::UserAuthInterfaceProxy::BeginIdentification_(contextId, authType, challenge, executorSensorHint, scheduleInfo, GetCurrentRemote());
}

int32_t OHOS::HDI::UserAuth::V4_1::UserAuthInterfaceProxy::GetAllUserInfo(std::vector<OHOS::HDI::UserAuth::V4_0::UserInfo>& userInfos)
{
    return OHOS::HDI::UserAuth::V4_0::UserAuthInterfaceProxy::GetAllUserInfo_(userInfos, GetCurrentRemote());
}

int32_t OHOS::HDI::UserAuth::V4_1::UserAuthInterfaceProxy::GetAllExtUserInfo(std::vector<OHOS::HDI::UserAuth::V4_0::ExtUserInfo>& userInfos)
{
    return OHOS::HDI::UserAuth::V4_0::UserAuthInterfaceProxy::GetAllExtUserInfo_(userInfos, GetCurrentRemote());
}

int32_t OHOS::HDI::UserAuth::V4_1::UserAuthInterfaceProxy::GetEnrolledState(int32_t userId, int32_t authType,
     OHOS::HDI::UserAuth::V4_0::EnrolledState& enrolledState)
{
    return OHOS::HDI::UserAuth::V4_0::UserAuthInterfaceProxy::GetEnrolledState_(userId, authType, enrolledState, GetCurrentRemote());
}

int32_t OHOS::HDI::UserAuth::V4_1::UserAuthInterfaceProxy::CheckReuseUnlockResult(const OHOS::HDI::UserAuth::V4_0::ReuseUnlockParam& reuseParam, OHOS::HDI::UserAuth::V4_0::ReuseUnlockInfo& reuseInfo)
{
    return OHOS::HDI::UserAuth::V4_0::UserAuthInterfaceProxy::CheckReuseUnlockResult_(reuseParam, reuseInfo, GetCurrentRemote());
}

int32_t OHOS::HDI::UserAuth::V4_1::UserAuthInterfaceProxy::SendMessage(uint64_t scheduleId, int32_t srcRole,
     const std::vector<uint8_t>& msg)
{
    return OHOS::HDI::UserAuth::V4_0::UserAuthInterfaceProxy::SendMessage_(scheduleId, srcRole, msg, GetCurrentRemote());
}

int32_t OHOS::HDI::UserAuth::V4_1::UserAuthInterfaceProxy::RegisterMessageCallback(const sptr<OHOS::HDI::UserAuth::V4_0::IMessageCallback>& messageCallback)
{
    return OHOS::HDI::UserAuth::V4_0::UserAuthInterfaceProxy::RegisterMessageCallback_(messageCallback, GetCurrentRemote());
}

int32_t OHOS::HDI::UserAuth::V4_1::UserAuthInterfaceProxy::PrepareRemoteAuth(const std::string& remoteUdid)
{
    return OHOS::HDI::UserAuth::V4_0::UserAuthInterfaceProxy::PrepareRemoteAuth_(remoteUdid, GetCurrentRemote());
}

int32_t OHOS::HDI::UserAuth::V4_1::UserAuthInterfaceProxy::GetLocalScheduleFromMessage(const std::string& remoteUdid,
     const std::vector<uint8_t>& message, OHOS::HDI::UserAuth::V4_0::ScheduleInfo& scheduleInfo)
{
    return OHOS::HDI::UserAuth::V4_0::UserAuthInterfaceProxy::GetLocalScheduleFromMessage_(remoteUdid, message, scheduleInfo, GetCurrentRemote());
}

int32_t OHOS::HDI::UserAuth::V4_1::UserAuthInterfaceProxy::GetSignedExecutorInfo(const std::vector<int32_t>& authTypes,
     int32_t executorRole, const std::string& remoteUdid, std::vector<uint8_t>& signedExecutorInfo)
{
    return OHOS::HDI::UserAuth::V4_0::UserAuthInterfaceProxy::GetSignedExecutorInfo_(authTypes, executorRole, remoteUdid, signedExecutorInfo, GetCurrentRemote());
}

int32_t OHOS::HDI::UserAuth::V4_1::UserAuthInterfaceProxy::GetAuthResultFromMessage(const std::string& remoteUdid,
     const std::vector<uint8_t>& message, OHOS::HDI::UserAuth::V4_0::AuthResultInfo& authResultInfo)
{
    return OHOS::HDI::UserAuth::V4_0::UserAuthInterfaceProxy::GetAuthResultFromMessage_(remoteUdid, message, authResultInfo, GetCurrentRemote());
}

int32_t OHOS::HDI::UserAuth::V4_1::UserAuthInterfaceProxy::SetGlobalConfigParam(const OHOS::HDI::UserAuth::V4_0::GlobalConfigParam& param)
{
    return OHOS::HDI::UserAuth::V4_0::UserAuthInterfaceProxy::SetGlobalConfigParam_(param, GetCurrentRemote());
}

int32_t OHOS::HDI::UserAuth::V4_1::UserAuthInterfaceProxy::GetCredentialById(uint64_t credentialId,
     OHOS::HDI::UserAuth::V4_0::CredentialInfo& info)
{
    return OHOS::HDI::UserAuth::V4_0::UserAuthInterfaceProxy::GetCredentialById_(credentialId, info, GetCurrentRemote());
}

int32_t OHOS::HDI::UserAuth::V4_1::UserAuthInterfaceProxy::VerifyAuthToken(const std::vector<uint8_t>& tokenIn,
     uint64_t allowableDuration, OHOS::HDI::UserAuth::V4_0::UserAuthTokenPlain& tokenPlainOut, std::vector<uint8_t>& rootSecret)
{
    return OHOS::HDI::UserAuth::V4_0::UserAuthInterfaceProxy::VerifyAuthToken_(tokenIn, allowableDuration, tokenPlainOut, rootSecret, GetCurrentRemote());
}

int32_t OHOS::HDI::UserAuth::V4_1::UserAuthInterfaceProxy::UpdateAbandonResult(int32_t userId,
     const std::vector<uint8_t>& scheduleResult, std::vector<OHOS::HDI::UserAuth::V4_0::CredentialInfo>& infos)
{
    return OHOS::HDI::UserAuth::V4_0::UserAuthInterfaceProxy::UpdateAbandonResult_(userId, scheduleResult, infos, GetCurrentRemote());
}

int32_t OHOS::HDI::UserAuth::V4_1::UserAuthInterfaceProxy::ClearUnavailableCredential(const std::vector<int32_t>& userIds, std::vector<OHOS::HDI::UserAuth::V4_0::CredentialInfo>& infos)
{
    return OHOS::HDI::UserAuth::V4_0::UserAuthInterfaceProxy::ClearUnavailableCredential_(userIds, infos, GetCurrentRemote());
}

int32_t OHOS::HDI::UserAuth::V4_1::UserAuthInterfaceProxy::GetVersion(uint32_t& majorVer, uint32_t& minorVer)
{
    return OHOS::HDI::UserAuth::V4_0::UserAuthInterfaceProxy::GetVersion_(majorVer, minorVer, GetCurrentRemote());
}

int32_t OHOS::HDI::UserAuth::V4_1::UserAuthInterfaceProxy::BeginAuthenticationExt_(uint64_t contextId,
     const OHOS::HDI::UserAuth::V4_1::AuthParamExt& param, std::vector<OHOS::HDI::UserAuth::V4_0::ScheduleInfo>& scheduleInfos, const sptr<IRemoteObject> remote)
{
    MessageParcel userAuthInterfaceData;
    MessageParcel userAuthInterfaceReply;
    MessageOption userAuthInterfaceOption(MessageOption::TF_SYNC);

    if (!userAuthInterfaceData.WriteInterfaceToken(OHOS::HDI::UserAuth::V4_1::IUserAuthInterface::GetDescriptor())) {
        HDF_LOGE("%{public}s: failed to write interface descriptor!", __func__);
        return HDF_ERR_INVALID_PARAM;
    }

    if (!userAuthInterfaceData.WriteBool(false)) {
        HDF_LOGE("%{public}s:failed to write flag of memory setting!", __func__);
        return HDF_ERR_INVALID_PARAM;
    }

    if (!userAuthInterfaceData.WriteUint64(contextId)) {
        HDF_LOGE("%{public}s: write contextId failed!", __func__);
        return HDF_ERR_INVALID_PARAM;
    }

    if (!OHOS::HDI::UserAuth::V4_1::AuthParamExtBlockMarshalling(userAuthInterfaceData, param)) {
        HDF_LOGE("%{public}s: write param failed!", __func__);
        return HDF_ERR_INVALID_PARAM;
    }

    if (remote == nullptr) {
        HDF_LOGE("%{public}s: invalid remote object!", __func__);
        return HDF_ERR_INVALID_OBJECT;
    }

    int32_t userAuthInterfaceRet = remote->SendRequest(CMD_USER_AUTH_INTERFACE_BEGIN_AUTHENTICATION_EXT, userAuthInterfaceData, userAuthInterfaceReply, userAuthInterfaceOption);
    if (userAuthInterfaceRet != HDF_SUCCESS) {
        HDF_LOGE("%{public}s failed, error code is %{public}d", __func__, userAuthInterfaceRet);
        return userAuthInterfaceRet;
    }

    uint32_t scheduleInfosSize = 0;
    if (!userAuthInterfaceReply.ReadUint32(scheduleInfosSize)) {
        HDF_LOGE("%{public}s: failed to read size", __func__);
        return HDF_ERR_INVALID_PARAM;
    }

    HDI_CHECK_VALUE_RETURN(scheduleInfosSize, >, HDI_BUFF_MAX_SIZE / sizeof(OHOS::HDI::UserAuth::V4_0::ScheduleInfo), HDF_ERR_INVALID_PARAM);
    scheduleInfos.clear();
    scheduleInfos.reserve(scheduleInfosSize);
    for (uint32_t i0 = 0; i0 < scheduleInfosSize; ++i0) {
        OHOS::HDI::UserAuth::V4_0::ScheduleInfo value0;
        if (!ScheduleInfoBlockUnmarshalling(userAuthInterfaceReply, value0)) {
            HDF_LOGE("%{public}s: read value0 failed!", __func__);
            return HDF_ERR_INVALID_PARAM;
        }
        scheduleInfos.push_back(value0);
    }

    return userAuthInterfaceRet;
}

int32_t OHOS::HDI::UserAuth::V4_1::UserAuthInterfaceProxy::BeginEnrollmentExt_(const std::vector<uint8_t>& authToken,
     const OHOS::HDI::UserAuth::V4_1::EnrollParamExt& param, OHOS::HDI::UserAuth::V4_0::ScheduleInfo& info, const sptr<IRemoteObject> remote)
{
    MessageParcel userAuthInterfaceData;
    MessageParcel userAuthInterfaceReply;
    MessageOption userAuthInterfaceOption(MessageOption::TF_SYNC);

    if (!userAuthInterfaceData.WriteInterfaceToken(OHOS::HDI::UserAuth::V4_1::IUserAuthInterface::GetDescriptor())) {
        HDF_LOGE("%{public}s: failed to write interface descriptor!", __func__);
        return HDF_ERR_INVALID_PARAM;
    }

    if (!WritePodArray(userAuthInterfaceData, authToken)) {
        HDF_LOGE("%{public}s: failed to write authToken", __func__);
        return HDF_ERR_INVALID_PARAM;
    }

    if (!OHOS::HDI::UserAuth::V4_1::EnrollParamExtBlockMarshalling(userAuthInterfaceData, param)) {
        HDF_LOGE("%{public}s: write param failed!", __func__);
        return HDF_ERR_INVALID_PARAM;
    }

    if (remote == nullptr) {
        HDF_LOGE("%{public}s: invalid remote object!", __func__);
        return HDF_ERR_INVALID_OBJECT;
    }

    int32_t userAuthInterfaceRet = remote->SendRequest(CMD_USER_AUTH_INTERFACE_BEGIN_ENROLLMENT_EXT, userAuthInterfaceData, userAuthInterfaceReply, userAuthInterfaceOption);
    if (userAuthInterfaceRet != HDF_SUCCESS) {
        HDF_LOGE("%{public}s failed, error code is %{public}d", __func__, userAuthInterfaceRet);
        return userAuthInterfaceRet;
    }

    if (!ScheduleInfoBlockUnmarshalling(userAuthInterfaceReply, info)) {
        HDF_LOGE("%{public}s: read info failed!", __func__);
        return HDF_ERR_INVALID_PARAM;
    }

    return userAuthInterfaceRet;
}

} // V4_1
} // UserAuth
} // HDI
} // OHOS
