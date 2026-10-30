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

#include <hdf_base.h>
#include <hdf_core_log.h>
#include <hdf_device_desc.h>
#include <hdf_sbuf_ipc.h>
#include "v4_1/user_auth_interface_stub.h"

#define HDF_LOG_TAG    user_auth_interface_driver

using namespace OHOS::HDI::UserAuth::V4_1;

struct HdfUserAuthInterfaceHost {
    struct IDeviceIoService ioService;
    OHOS::sptr<OHOS::IRemoteObject> stub;
};

static int32_t UserAuthInterfaceDriverDispatch(struct HdfDeviceIoClient *client, int cmdId, struct HdfSBuf *data,
    struct HdfSBuf *reply)
{
    auto *hdfUserAuthInterfaceHost = CONTAINER_OF(client->device->service, struct HdfUserAuthInterfaceHost, ioService);

    OHOS::MessageParcel *dataParcel = nullptr;
    OHOS::MessageParcel *replyParcel = nullptr;
    OHOS::MessageOption option;

    if (SbufToParcel(data, &dataParcel) != HDF_SUCCESS) {
        HDF_LOGE("%{public}s: invalid data sbuf object to dispatch", __func__);
        return HDF_ERR_INVALID_PARAM;
    }
    if (SbufToParcel(reply, &replyParcel) != HDF_SUCCESS) {
        HDF_LOGE("%{public}s: invalid reply sbuf object to dispatch", __func__);
        return HDF_ERR_INVALID_PARAM;
    }

    return hdfUserAuthInterfaceHost->stub->SendRequest(cmdId, *dataParcel, *replyParcel, option);
}

static int HdfUserAuthInterfaceDriverInit(struct HdfDeviceObject *deviceObject)
{
    HDF_LOGI("%{public}s: driver init start", __func__);
    return HDF_SUCCESS;
}

static int HdfUserAuthInterfaceDriverBind(struct HdfDeviceObject *deviceObject)
{
    HDF_LOGI("%{public}s: driver bind start", __func__);
    auto *hdfUserAuthInterfaceHost = new (std::nothrow) HdfUserAuthInterfaceHost;
    if (hdfUserAuthInterfaceHost == nullptr) {
        HDF_LOGE("%{public}s: failed to create create HdfUserAuthInterfaceHost object", __func__);
        return HDF_FAILURE;
    }

    hdfUserAuthInterfaceHost->ioService.Dispatch = UserAuthInterfaceDriverDispatch;
    hdfUserAuthInterfaceHost->ioService.Open = NULL;
    hdfUserAuthInterfaceHost->ioService.Release = NULL;

    auto serviceImpl = OHOS::HDI::UserAuth::V4_1::IUserAuthInterface::Get(true);
    if (serviceImpl == nullptr) {
        HDF_LOGE("%{public}s: failed to get of implement service", __func__);
        delete hdfUserAuthInterfaceHost;
        return HDF_FAILURE;
    }

    hdfUserAuthInterfaceHost->stub = OHOS::HDI::ObjectCollector::GetInstance().GetOrNewObject(serviceImpl,
        OHOS::HDI::UserAuth::V4_1::IUserAuthInterface::GetDescriptor());
    if (hdfUserAuthInterfaceHost->stub == nullptr) {
        HDF_LOGE("%{public}s: failed to get stub object", __func__);
        delete hdfUserAuthInterfaceHost;
        return HDF_FAILURE;
    }

    deviceObject->service = &hdfUserAuthInterfaceHost->ioService;
    return HDF_SUCCESS;
}

static void HdfUserAuthInterfaceDriverRelease(struct HdfDeviceObject *deviceObject)
{
    HDF_LOGI("%{public}s: driver release start", __func__);
    if (deviceObject->service == nullptr) {
        return;
    }

    auto *hdfUserAuthInterfaceHost = CONTAINER_OF(deviceObject->service, struct HdfUserAuthInterfaceHost, ioService);
    if (hdfUserAuthInterfaceHost != nullptr) {
        delete hdfUserAuthInterfaceHost;
    }
}

struct HdfDriverEntry g_userauthinterfaceDriverEntry = {
    .moduleVersion = 1,
    .moduleName = "",
    .Bind = HdfUserAuthInterfaceDriverBind,
    .Init = HdfUserAuthInterfaceDriverInit,
    .Release = HdfUserAuthInterfaceDriverRelease,
};

#ifdef __cplusplus
extern "C" {
#endif /* __cplusplus */
HDF_INIT(g_userauthinterfaceDriverEntry);
#ifdef __cplusplus
}
#endif /* __cplusplus */
