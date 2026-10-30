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

#ifndef OHOS_HDI_USER_AUTH_V4_0_USERAUTHINTERFACESTUB_H
#define OHOS_HDI_USER_AUTH_V4_0_USERAUTHINTERFACESTUB_H

#include <ipc_object_stub.h>
#include <message_option.h>
#include <message_parcel.h>
#include <object_collector.h>
#include <refbase.h>
#include "v4_0/iuser_auth_interface.h"

namespace OHOS {
namespace HDI {
namespace UserAuth {
namespace V4_0 {

using namespace OHOS;
class UserAuthInterfaceStub : public IPCObjectStub {
public:
    explicit UserAuthInterfaceStub(const sptr<IUserAuthInterface> &impl);
    virtual ~UserAuthInterfaceStub();

    int32_t OnRemoteRequest(uint32_t code, MessageParcel &data, MessageParcel &reply, MessageOption &option) override;

    static int32_t UserAuthInterfaceStubInit_(MessageParcel& userAuthInterfaceData, MessageParcel& userAuthInterfaceReply, MessageOption& userAuthInterfaceOption, sptr<OHOS::HDI::UserAuth::V4_0::IUserAuthInterface> impl);

    static int32_t UserAuthInterfaceStubAddExecutor_(MessageParcel& userAuthInterfaceData, MessageParcel& userAuthInterfaceReply, MessageOption& userAuthInterfaceOption, sptr<OHOS::HDI::UserAuth::V4_0::IUserAuthInterface> impl);

    static int32_t UserAuthInterfaceStubDeleteExecutor_(MessageParcel& userAuthInterfaceData, MessageParcel& userAuthInterfaceReply, MessageOption& userAuthInterfaceOption, sptr<OHOS::HDI::UserAuth::V4_0::IUserAuthInterface> impl);

    static int32_t UserAuthInterfaceStubOpenSession_(MessageParcel& userAuthInterfaceData, MessageParcel& userAuthInterfaceReply, MessageOption& userAuthInterfaceOption, sptr<OHOS::HDI::UserAuth::V4_0::IUserAuthInterface> impl);

    static int32_t UserAuthInterfaceStubCloseSession_(MessageParcel& userAuthInterfaceData, MessageParcel& userAuthInterfaceReply, MessageOption& userAuthInterfaceOption, sptr<OHOS::HDI::UserAuth::V4_0::IUserAuthInterface> impl);

    static int32_t UserAuthInterfaceStubUpdateEnrollmentResult_(MessageParcel& userAuthInterfaceData, MessageParcel& userAuthInterfaceReply, MessageOption& userAuthInterfaceOption, sptr<OHOS::HDI::UserAuth::V4_0::IUserAuthInterface> impl);

    static int32_t UserAuthInterfaceStubCancelEnrollment_(MessageParcel& userAuthInterfaceData, MessageParcel& userAuthInterfaceReply, MessageOption& userAuthInterfaceOption, sptr<OHOS::HDI::UserAuth::V4_0::IUserAuthInterface> impl);

    static int32_t UserAuthInterfaceStubDeleteCredential_(MessageParcel& userAuthInterfaceData, MessageParcel& userAuthInterfaceReply, MessageOption& userAuthInterfaceOption, sptr<OHOS::HDI::UserAuth::V4_0::IUserAuthInterface> impl);

    static int32_t UserAuthInterfaceStubGetCredential_(MessageParcel& userAuthInterfaceData, MessageParcel& userAuthInterfaceReply, MessageOption& userAuthInterfaceOption, sptr<OHOS::HDI::UserAuth::V4_0::IUserAuthInterface> impl);

    static int32_t UserAuthInterfaceStubGetUserInfo_(MessageParcel& userAuthInterfaceData, MessageParcel& userAuthInterfaceReply, MessageOption& userAuthInterfaceOption, sptr<OHOS::HDI::UserAuth::V4_0::IUserAuthInterface> impl);

    static int32_t UserAuthInterfaceStubDeleteUser_(MessageParcel& userAuthInterfaceData, MessageParcel& userAuthInterfaceReply, MessageOption& userAuthInterfaceOption, sptr<OHOS::HDI::UserAuth::V4_0::IUserAuthInterface> impl);

    static int32_t UserAuthInterfaceStubEnforceDeleteUser_(MessageParcel& userAuthInterfaceData, MessageParcel& userAuthInterfaceReply, MessageOption& userAuthInterfaceOption, sptr<OHOS::HDI::UserAuth::V4_0::IUserAuthInterface> impl);

    static int32_t UserAuthInterfaceStubUpdateAuthenticationResult_(MessageParcel& userAuthInterfaceData, MessageParcel& userAuthInterfaceReply, MessageOption& userAuthInterfaceOption, sptr<OHOS::HDI::UserAuth::V4_0::IUserAuthInterface> impl);

    static int32_t UserAuthInterfaceStubCancelAuthentication_(MessageParcel& userAuthInterfaceData, MessageParcel& userAuthInterfaceReply, MessageOption& userAuthInterfaceOption, sptr<OHOS::HDI::UserAuth::V4_0::IUserAuthInterface> impl);

    static int32_t UserAuthInterfaceStubUpdateIdentificationResult_(MessageParcel& userAuthInterfaceData, MessageParcel& userAuthInterfaceReply, MessageOption& userAuthInterfaceOption, sptr<OHOS::HDI::UserAuth::V4_0::IUserAuthInterface> impl);

    static int32_t UserAuthInterfaceStubCancelIdentification_(MessageParcel& userAuthInterfaceData, MessageParcel& userAuthInterfaceReply, MessageOption& userAuthInterfaceOption, sptr<OHOS::HDI::UserAuth::V4_0::IUserAuthInterface> impl);

    static int32_t UserAuthInterfaceStubGetAvailableStatus_(MessageParcel& userAuthInterfaceData, MessageParcel& userAuthInterfaceReply, MessageOption& userAuthInterfaceOption, sptr<OHOS::HDI::UserAuth::V4_0::IUserAuthInterface> impl);

    static int32_t UserAuthInterfaceStubGetValidSolution_(MessageParcel& userAuthInterfaceData, MessageParcel& userAuthInterfaceReply, MessageOption& userAuthInterfaceOption, sptr<OHOS::HDI::UserAuth::V4_0::IUserAuthInterface> impl);

    static int32_t UserAuthInterfaceStubBeginAuthentication_(MessageParcel& userAuthInterfaceData, MessageParcel& userAuthInterfaceReply, MessageOption& userAuthInterfaceOption, sptr<OHOS::HDI::UserAuth::V4_0::IUserAuthInterface> impl);

    static int32_t UserAuthInterfaceStubBeginEnrollment_(MessageParcel& userAuthInterfaceData, MessageParcel& userAuthInterfaceReply, MessageOption& userAuthInterfaceOption, sptr<OHOS::HDI::UserAuth::V4_0::IUserAuthInterface> impl);

    static int32_t UserAuthInterfaceStubBeginIdentification_(MessageParcel& userAuthInterfaceData, MessageParcel& userAuthInterfaceReply, MessageOption& userAuthInterfaceOption, sptr<OHOS::HDI::UserAuth::V4_0::IUserAuthInterface> impl);

    static int32_t UserAuthInterfaceStubGetAllUserInfo_(MessageParcel& userAuthInterfaceData, MessageParcel& userAuthInterfaceReply, MessageOption& userAuthInterfaceOption, sptr<OHOS::HDI::UserAuth::V4_0::IUserAuthInterface> impl);

    static int32_t UserAuthInterfaceStubGetAllExtUserInfo_(MessageParcel& userAuthInterfaceData, MessageParcel& userAuthInterfaceReply, MessageOption& userAuthInterfaceOption, sptr<OHOS::HDI::UserAuth::V4_0::IUserAuthInterface> impl);

    static int32_t UserAuthInterfaceStubGetEnrolledState_(MessageParcel& userAuthInterfaceData, MessageParcel& userAuthInterfaceReply, MessageOption& userAuthInterfaceOption, sptr<OHOS::HDI::UserAuth::V4_0::IUserAuthInterface> impl);

    static int32_t UserAuthInterfaceStubCheckReuseUnlockResult_(MessageParcel& userAuthInterfaceData, MessageParcel& userAuthInterfaceReply, MessageOption& userAuthInterfaceOption, sptr<OHOS::HDI::UserAuth::V4_0::IUserAuthInterface> impl);

    static int32_t UserAuthInterfaceStubSendMessage_(MessageParcel& userAuthInterfaceData, MessageParcel& userAuthInterfaceReply, MessageOption& userAuthInterfaceOption, sptr<OHOS::HDI::UserAuth::V4_0::IUserAuthInterface> impl);

    static int32_t UserAuthInterfaceStubRegisterMessageCallback_(MessageParcel& userAuthInterfaceData, MessageParcel& userAuthInterfaceReply, MessageOption& userAuthInterfaceOption, sptr<OHOS::HDI::UserAuth::V4_0::IUserAuthInterface> impl);

    static int32_t UserAuthInterfaceStubPrepareRemoteAuth_(MessageParcel& userAuthInterfaceData, MessageParcel& userAuthInterfaceReply, MessageOption& userAuthInterfaceOption, sptr<OHOS::HDI::UserAuth::V4_0::IUserAuthInterface> impl);

    static int32_t UserAuthInterfaceStubGetLocalScheduleFromMessage_(MessageParcel& userAuthInterfaceData, MessageParcel& userAuthInterfaceReply, MessageOption& userAuthInterfaceOption, sptr<OHOS::HDI::UserAuth::V4_0::IUserAuthInterface> impl);

    static int32_t UserAuthInterfaceStubGetSignedExecutorInfo_(MessageParcel& userAuthInterfaceData, MessageParcel& userAuthInterfaceReply, MessageOption& userAuthInterfaceOption, sptr<OHOS::HDI::UserAuth::V4_0::IUserAuthInterface> impl);

    static int32_t UserAuthInterfaceStubGetAuthResultFromMessage_(MessageParcel& userAuthInterfaceData, MessageParcel& userAuthInterfaceReply, MessageOption& userAuthInterfaceOption, sptr<OHOS::HDI::UserAuth::V4_0::IUserAuthInterface> impl);

    static int32_t UserAuthInterfaceStubSetGlobalConfigParam_(MessageParcel& userAuthInterfaceData, MessageParcel& userAuthInterfaceReply, MessageOption& userAuthInterfaceOption, sptr<OHOS::HDI::UserAuth::V4_0::IUserAuthInterface> impl);

    static int32_t UserAuthInterfaceStubGetCredentialById_(MessageParcel& userAuthInterfaceData, MessageParcel& userAuthInterfaceReply, MessageOption& userAuthInterfaceOption, sptr<OHOS::HDI::UserAuth::V4_0::IUserAuthInterface> impl);

    static int32_t UserAuthInterfaceStubVerifyAuthToken_(MessageParcel& userAuthInterfaceData, MessageParcel& userAuthInterfaceReply, MessageOption& userAuthInterfaceOption, sptr<OHOS::HDI::UserAuth::V4_0::IUserAuthInterface> impl);

    static int32_t UserAuthInterfaceStubUpdateAbandonResult_(MessageParcel& userAuthInterfaceData, MessageParcel& userAuthInterfaceReply, MessageOption& userAuthInterfaceOption, sptr<OHOS::HDI::UserAuth::V4_0::IUserAuthInterface> impl);

    static int32_t UserAuthInterfaceStubClearUnavailableCredential_(MessageParcel& userAuthInterfaceData, MessageParcel& userAuthInterfaceReply, MessageOption& userAuthInterfaceOption, sptr<OHOS::HDI::UserAuth::V4_0::IUserAuthInterface> impl);

    static int32_t UserAuthInterfaceStubGetVersion_(MessageParcel& userAuthInterfaceData, MessageParcel& userAuthInterfaceReply, MessageOption& userAuthInterfaceOption, sptr<OHOS::HDI::UserAuth::V4_0::IUserAuthInterface> impl);

private:
    int32_t UserAuthInterfaceStubInit(MessageParcel& userAuthInterfaceData, MessageParcel& userAuthInterfaceReply, MessageOption& userAuthInterfaceOption);

    int32_t UserAuthInterfaceStubAddExecutor(MessageParcel& userAuthInterfaceData, MessageParcel& userAuthInterfaceReply, MessageOption& userAuthInterfaceOption);

    int32_t UserAuthInterfaceStubDeleteExecutor(MessageParcel& userAuthInterfaceData, MessageParcel& userAuthInterfaceReply, MessageOption& userAuthInterfaceOption);

    int32_t UserAuthInterfaceStubOpenSession(MessageParcel& userAuthInterfaceData, MessageParcel& userAuthInterfaceReply, MessageOption& userAuthInterfaceOption);

    int32_t UserAuthInterfaceStubCloseSession(MessageParcel& userAuthInterfaceData, MessageParcel& userAuthInterfaceReply, MessageOption& userAuthInterfaceOption);

    int32_t UserAuthInterfaceStubUpdateEnrollmentResult(MessageParcel& userAuthInterfaceData, MessageParcel& userAuthInterfaceReply, MessageOption& userAuthInterfaceOption);

    int32_t UserAuthInterfaceStubCancelEnrollment(MessageParcel& userAuthInterfaceData, MessageParcel& userAuthInterfaceReply, MessageOption& userAuthInterfaceOption);

    int32_t UserAuthInterfaceStubDeleteCredential(MessageParcel& userAuthInterfaceData, MessageParcel& userAuthInterfaceReply, MessageOption& userAuthInterfaceOption);

    int32_t UserAuthInterfaceStubGetCredential(MessageParcel& userAuthInterfaceData, MessageParcel& userAuthInterfaceReply, MessageOption& userAuthInterfaceOption);

    int32_t UserAuthInterfaceStubGetUserInfo(MessageParcel& userAuthInterfaceData, MessageParcel& userAuthInterfaceReply, MessageOption& userAuthInterfaceOption);

    int32_t UserAuthInterfaceStubDeleteUser(MessageParcel& userAuthInterfaceData, MessageParcel& userAuthInterfaceReply, MessageOption& userAuthInterfaceOption);

    int32_t UserAuthInterfaceStubEnforceDeleteUser(MessageParcel& userAuthInterfaceData, MessageParcel& userAuthInterfaceReply, MessageOption& userAuthInterfaceOption);

    int32_t UserAuthInterfaceStubUpdateAuthenticationResult(MessageParcel& userAuthInterfaceData, MessageParcel& userAuthInterfaceReply, MessageOption& userAuthInterfaceOption);

    int32_t UserAuthInterfaceStubCancelAuthentication(MessageParcel& userAuthInterfaceData, MessageParcel& userAuthInterfaceReply, MessageOption& userAuthInterfaceOption);

    int32_t UserAuthInterfaceStubUpdateIdentificationResult(MessageParcel& userAuthInterfaceData, MessageParcel& userAuthInterfaceReply, MessageOption& userAuthInterfaceOption);

    int32_t UserAuthInterfaceStubCancelIdentification(MessageParcel& userAuthInterfaceData, MessageParcel& userAuthInterfaceReply, MessageOption& userAuthInterfaceOption);

    int32_t UserAuthInterfaceStubGetAvailableStatus(MessageParcel& userAuthInterfaceData, MessageParcel& userAuthInterfaceReply, MessageOption& userAuthInterfaceOption);

    int32_t UserAuthInterfaceStubGetValidSolution(MessageParcel& userAuthInterfaceData, MessageParcel& userAuthInterfaceReply, MessageOption& userAuthInterfaceOption);

    int32_t UserAuthInterfaceStubBeginAuthentication(MessageParcel& userAuthInterfaceData, MessageParcel& userAuthInterfaceReply, MessageOption& userAuthInterfaceOption);

    int32_t UserAuthInterfaceStubBeginEnrollment(MessageParcel& userAuthInterfaceData, MessageParcel& userAuthInterfaceReply, MessageOption& userAuthInterfaceOption);

    int32_t UserAuthInterfaceStubBeginIdentification(MessageParcel& userAuthInterfaceData, MessageParcel& userAuthInterfaceReply, MessageOption& userAuthInterfaceOption);

    int32_t UserAuthInterfaceStubGetAllUserInfo(MessageParcel& userAuthInterfaceData, MessageParcel& userAuthInterfaceReply, MessageOption& userAuthInterfaceOption);

    int32_t UserAuthInterfaceStubGetAllExtUserInfo(MessageParcel& userAuthInterfaceData, MessageParcel& userAuthInterfaceReply, MessageOption& userAuthInterfaceOption);

    int32_t UserAuthInterfaceStubGetEnrolledState(MessageParcel& userAuthInterfaceData, MessageParcel& userAuthInterfaceReply, MessageOption& userAuthInterfaceOption);

    int32_t UserAuthInterfaceStubCheckReuseUnlockResult(MessageParcel& userAuthInterfaceData, MessageParcel& userAuthInterfaceReply, MessageOption& userAuthInterfaceOption);

    int32_t UserAuthInterfaceStubSendMessage(MessageParcel& userAuthInterfaceData, MessageParcel& userAuthInterfaceReply, MessageOption& userAuthInterfaceOption);

    int32_t UserAuthInterfaceStubRegisterMessageCallback(MessageParcel& userAuthInterfaceData, MessageParcel& userAuthInterfaceReply, MessageOption& userAuthInterfaceOption);

    int32_t UserAuthInterfaceStubPrepareRemoteAuth(MessageParcel& userAuthInterfaceData, MessageParcel& userAuthInterfaceReply, MessageOption& userAuthInterfaceOption);

    int32_t UserAuthInterfaceStubGetLocalScheduleFromMessage(MessageParcel& userAuthInterfaceData, MessageParcel& userAuthInterfaceReply, MessageOption& userAuthInterfaceOption);

    int32_t UserAuthInterfaceStubGetSignedExecutorInfo(MessageParcel& userAuthInterfaceData, MessageParcel& userAuthInterfaceReply, MessageOption& userAuthInterfaceOption);

    int32_t UserAuthInterfaceStubGetAuthResultFromMessage(MessageParcel& userAuthInterfaceData, MessageParcel& userAuthInterfaceReply, MessageOption& userAuthInterfaceOption);

    int32_t UserAuthInterfaceStubSetGlobalConfigParam(MessageParcel& userAuthInterfaceData, MessageParcel& userAuthInterfaceReply, MessageOption& userAuthInterfaceOption);

    int32_t UserAuthInterfaceStubGetCredentialById(MessageParcel& userAuthInterfaceData, MessageParcel& userAuthInterfaceReply, MessageOption& userAuthInterfaceOption);

    int32_t UserAuthInterfaceStubVerifyAuthToken(MessageParcel& userAuthInterfaceData, MessageParcel& userAuthInterfaceReply, MessageOption& userAuthInterfaceOption);

    int32_t UserAuthInterfaceStubUpdateAbandonResult(MessageParcel& userAuthInterfaceData, MessageParcel& userAuthInterfaceReply, MessageOption& userAuthInterfaceOption);

    int32_t UserAuthInterfaceStubClearUnavailableCredential(MessageParcel& userAuthInterfaceData, MessageParcel& userAuthInterfaceReply, MessageOption& userAuthInterfaceOption);

    int32_t UserAuthInterfaceStubGetVersion(MessageParcel& userAuthInterfaceData, MessageParcel& userAuthInterfaceReply, MessageOption& userAuthInterfaceOption);


    static inline ObjectDelegator<OHOS::HDI::UserAuth::V4_0::UserAuthInterfaceStub, OHOS::HDI::UserAuth::V4_0::IUserAuthInterface> objDelegator_;
    sptr<OHOS::HDI::UserAuth::V4_0::IUserAuthInterface> impl_;
};
} // V4_0
} // UserAuth
} // HDI
} // OHOS

#endif // OHOS_HDI_USER_AUTH_V4_0_USERAUTHINTERFACESTUB_H