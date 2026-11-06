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

#ifndef OHOS_HDI_SENSOR_V3_1_SENSORINTERFACESERVICE_H
#define OHOS_HDI_SENSOR_V3_1_SENSORINTERFACESERVICE_H

#include "v3_1/isensor_interface.h"
#include <memory>

namespace OHOS {
namespace HDI {
namespace Sensor {
namespace V3_1 {
class SensorInterfaceService : public OHOS::HDI::Sensor::V3_1::ISensorInterface {
public:
    SensorInterfaceService();
    virtual ~SensorInterfaceService();
    int32_t Shutdown();

    int32_t EnableWithCallbackId(const OHOS::HDI::Sensor::V3_0::DeviceSensorInfo& deviceSensorInfo,
         uint32_t callbackId) override;

    int32_t DisableWithCallbackId(const OHOS::HDI::Sensor::V3_0::DeviceSensorInfo& deviceSensorInfo,
         uint32_t callbackId) override;

    int32_t SetBatchWithCallbackId(const OHOS::HDI::Sensor::V3_0::DeviceSensorInfo& deviceSensorInfo,
         uint32_t callbackId, int64_t samplingInterval, int64_t reportInterval) override;

    int32_t RegisterWithCallbackId(int32_t groupId, const sptr<OHOS::HDI::Sensor::V3_0::ISensorCallback>& callbackObj,
         uint32_t callbackId) override;

    int32_t UnregisterWithCallbackId(int32_t groupId, const sptr<OHOS::HDI::Sensor::V3_0::ISensorCallback>& callbackObj,
         uint32_t callbackId) override;

    int32_t GetAllSensorInfo(std::vector<OHOS::HDI::Sensor::V3_0::HdfSensorInformation>& info) override;

    int32_t GetDeviceSensorInfo(int32_t deviceId,
         std::vector<OHOS::HDI::Sensor::V3_0::HdfSensorInformation>& info) override;

    int32_t Enable(const OHOS::HDI::Sensor::V3_0::DeviceSensorInfo& deviceSensorInfo) override;

    int32_t Disable(const OHOS::HDI::Sensor::V3_0::DeviceSensorInfo& deviceSensorInfo) override;

    int32_t SetBatch(const OHOS::HDI::Sensor::V3_0::DeviceSensorInfo& deviceSensorInfo, int64_t samplingInterval,
         int64_t reportInterval) override;

    int32_t SetMode(const OHOS::HDI::Sensor::V3_0::DeviceSensorInfo& deviceSensorInfo, int32_t mode) override;

    int32_t SetOption(const OHOS::HDI::Sensor::V3_0::DeviceSensorInfo& deviceSensorInfo, uint32_t option) override;

    int32_t Register(int32_t groupId, const sptr<OHOS::HDI::Sensor::V3_0::ISensorCallback>& callbackObj) override;

    int32_t Unregister(int32_t groupId, const sptr<OHOS::HDI::Sensor::V3_0::ISensorCallback>& callbackObj) override;

    int32_t ReadData(const OHOS::HDI::Sensor::V3_0::DeviceSensorInfo& deviceSensorInfo,
         std::vector<OHOS::HDI::Sensor::V3_0::HdfSensorEvents>& event) override;

    int32_t SetSdcSensor(const OHOS::HDI::Sensor::V3_0::DeviceSensorInfo& deviceSensorInfo, bool enabled,
         int32_t rateLevel) override;

    int32_t GetSdcSensorInfo(std::vector<OHOS::HDI::Sensor::V3_0::SdcSensorInfo>& sdcSensorInfo) override;

    int32_t RegisterAsync(int32_t groupId, const sptr<OHOS::HDI::Sensor::V3_0::ISensorCallback>& callbackObj) override;

    int32_t UnregisterAsync(int32_t groupId,
         const sptr<OHOS::HDI::Sensor::V3_0::ISensorCallback>& callbackObj) override;

    int32_t RegSensorPlugCallBack(const sptr<OHOS::HDI::Sensor::V3_0::ISensorPlugCallback>& callbackObj) override;

    int32_t UnRegSensorPlugCallBack(const sptr<OHOS::HDI::Sensor::V3_0::ISensorPlugCallback>& callbackObj) override;

private:
    struct Impl;
    std::unique_ptr<Impl> impl_;
};
} // V3_1
} // Sensor
} // HDI
} // OHOS

#endif // OHOS_HDI_SENSOR_V3_1_SENSORINTERFACESERVICE_H