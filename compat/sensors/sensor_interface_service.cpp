#include "sensor_interface_service.h"
#include "ssc_backend.h"
#include "ssc_time.h"

#include <algorithm>
#include <array>
#include <atomic>
#include <cmath>
#include <cstring>
#include <iproxy_broker.h>
#include <map>
#include <mutex>
#include <set>
#include <time.h>

namespace OHOS::HDI::Sensor::V3_1 {
using namespace V3_0;

namespace {
constexpr uint64_t LEGACY_CLIENT = UINT64_MAX;
constexpr int64_t DEFAULT_INTERVAL_NS = 20000000;
constexpr int32_t LOCAL_DEVICE = -1;

DeviceSensorInfo Identity(uint32_t kind)
{
    return {LOCAL_DEVICE, static_cast<int32_t>(kind), 0, Location::LOCAL};
}

int32_t Result(int32_t result)
{
    return result == SSC_OK ? HDF_SUCCESS : HDF_FAILURE;
}
}

struct SensorInterfaceService::Impl {
    struct Stream {
        Impl *owner = nullptr;
        uint32_t kind = 0;
        SscBackend *backend = nullptr;
        SscSensorInfo info{};
        std::map<uint64_t, int64_t> intervals;
        std::set<uint64_t> enabled;
        bool discovered = false;
        bool running = false;
        float rate = 0.0f;
        std::atomic<int32_t> lastError{SSC_OK};
    };

    struct Client {
        sptr<ISensorCallback> callback;
        bool asynchronous = true;
        std::set<uint32_t> enabled;
    };

    // 启停锁与回调锁分离，停止线程时不阻塞数据回调
    std::mutex operationMutex;
    std::mutex callbackMutex;
    std::array<Stream, 2> streams;
    std::map<uint64_t, Client> clients;
    SscTime time{};
    bool timeReady = false;
    std::atomic<int64_t> nextTimeRefresh{0};
    std::atomic<bool> stopped{false};

    Impl()
    {
        timeReady = SscTimeInit(&time) == 0;
        for (size_t index = 0; index < streams.size(); ++index) {
            auto &stream = streams[index];
            stream.owner = this;
            stream.kind = index == 0 ? SSC_ACCEL : SSC_GYRO;
            SscBackendCreate(stream.kind, &stream.backend);
        }
    }

    ~Impl()
    {
        for (auto &stream : streams) {
            if (stream.backend != nullptr) {
                SscBackendDestroy(stream.backend);
            }
        }
        if (timeReady) {
            SscTimeDestroy(&time);
        }
    }

    Stream *Find(const DeviceSensorInfo &identity)
    {
        if (stopped.load()) {
            return nullptr;
        }
        for (auto &stream : streams) {
            const auto expected = Identity(stream.kind);
            if (identity.deviceId == expected.deviceId && identity.sensorType == expected.sensorType &&
                identity.sensorId == expected.sensorId && identity.location == expected.location) {
                return &stream;
            }
        }
        return nullptr;
    }

    int32_t Discover(Stream &stream)
    {
        if (stopped.load()) {
            return HDF_FAILURE;
        }
        if (stream.discovered) {
            return HDF_SUCCESS;
        }
        if (stream.backend == nullptr || SscBackendDiscover(stream.backend, &stream.info) != SSC_OK) {
            return HDF_FAILURE;
        }
        stream.discovered = stream.info.available && stream.info.type_matches;
        return stream.discovered ? HDF_SUCCESS : HDF_FAILURE;
    }

    static void OnError(const SscBackendError *error, void *context)
    {
        auto &stream = *static_cast<Stream *>(context);
        stream.lastError.store(error->result);
    }

    static void OnSample(const SscRawSample *sample, void *context)
    {
        auto &stream = *static_cast<Stream *>(context);
        auto &owner = *stream.owner;
        timespec now{};
        if (clock_gettime(CLOCK_BOOTTIME, &now) == 0) {
            int64_t current = now.tv_sec * INT64_C(1000000000) + now.tv_nsec;
            int64_t next = owner.nextTimeRefresh.load();
            if (current >= next) {
                if (SscTimeRefresh(&owner.time) != 0) {
                    return;
                }
                owner.nextTimeRefresh.store(current + SSC_TIME_REFRESH_PERIOD_NS);
            }
        }
        int64_t timestamp;
        if (!owner.timeReady || SscTimeConvert(&owner.time, sample->timestamp_ticks, &timestamp) != 0) {
            return;
        }
        HdfSensorEvents event{};
        event.deviceSensorInfo = Identity(stream.kind);
        event.version = 0;
        event.timestamp = timestamp;
        event.mode = 1;
        event.data.resize(sizeof(sample->values));
        // SSC已输出设备坐标系的工厂校准SI数值，不重复旋转或缩放
        std::memcpy(event.data.data(), sample->values, sizeof(sample->values));
        event.dataLen = event.data.size();
        std::vector<Client> recipients;
        {
            std::lock_guard<std::mutex> lock(owner.callbackMutex);
            for (const auto &[id, client] : owner.clients) {
                (void)id;
                if (client.enabled.count(stream.kind)) {
                    recipients.push_back(client);
                }
            }
        }
        // 复用原生HDI回调，不把到达时间冒充采样时间
        for (const auto &client : recipients) {
            if (client.asynchronous) {
                client.callback->OnDataEventAsync({event});
            } else {
                client.callback->OnDataEvent(event);
            }
        }
    }

    int32_t Apply(Stream &stream)
    {
        float rate = 0.0f;
        for (auto id : stream.enabled) {
            auto iterator = stream.intervals.find(id);
            int64_t interval = iterator == stream.intervals.end() ? DEFAULT_INTERVAL_NS : iterator->second;
            rate = std::max(rate, static_cast<float>(1000000000.0 / interval));
        }
        if (stream.running && rate == stream.rate) {
            uint32_t state;
            SscBackendError error{};
            if (SscBackendGetState(stream.backend, &state, &error) == SSC_OK && state == SSC_RUNNING) {
                return HDF_SUCCESS;
            }
        }
        if (stream.running) {
            int32_t stopped = SscBackendStop(stream.backend);
            stream.running = false;
            if (stopped != SSC_OK) {
                return HDF_FAILURE;
            }
        }
        stream.rate = rate;
        if (rate == 0.0f) {
            return HDF_SUCCESS;
        }
        SscBackendConfig config{rate};
        stream.lastError.store(SSC_OK);
        int32_t result = SscBackendStart(stream.backend, &config, OnSample, OnError, &stream);
        stream.running = result == SSC_OK;
        return Result(result);
    }

    int32_t Enable(const DeviceSensorInfo &identity, uint64_t id, bool enabled)
    {
        std::lock_guard<std::mutex> lock(operationMutex);
        auto *stream = Find(identity);
        if (stream == nullptr || !timeReady || Discover(*stream) != HDF_SUCCESS) {
            return HDF_ERR_INVALID_PARAM;
        }
        const auto previous = stream->enabled;
        {
            std::lock_guard<std::mutex> callbacks(callbackMutex);
            auto client = clients.find(id);
            if (client == clients.end()) {
                return HDF_ERR_INVALID_OBJECT;
            }
            if (enabled) {
                client->second.enabled.insert(stream->kind);
            } else {
                client->second.enabled.erase(stream->kind);
            }
        }
        if (enabled) {
            stream->enabled.insert(id);
        } else {
            stream->enabled.erase(id);
        }
        int32_t result = Apply(*stream);
        if (result != HDF_SUCCESS) {
            // 请求变更失败时恢复原订阅，再恢复原采样配置
            stream->enabled = previous;
            {
                std::lock_guard<std::mutex> callbacks(callbackMutex);
                if (previous.count(id)) {
                    clients[id].enabled.insert(stream->kind);
                } else {
                    clients[id].enabled.erase(stream->kind);
                }
            }
            Apply(*stream);
        }
        return result;
    }

    int32_t Batch(const DeviceSensorInfo &identity, uint64_t id, int64_t sampling, int64_t report)
    {
        std::lock_guard<std::mutex> lock(operationMutex);
        auto *stream = Find(identity);
        if (stream == nullptr || sampling <= 0 || report < 0) {
            return HDF_ERR_INVALID_PARAM;
        }
        // 逐帧交付满足最大上报延迟，不额外积压批次
        const auto previous = stream->intervals;
        stream->intervals[id] = sampling;
        int32_t result = stream->enabled.count(id) ? Apply(*stream) : HDF_SUCCESS;
        if (result != HDF_SUCCESS) {
            stream->intervals = previous;
            Apply(*stream);
        }
        return result;
    }

    int32_t Register(int32_t group, const sptr<ISensorCallback> &callback, uint64_t id, bool asynchronous)
    {
        if (group != HDF_TRADITIONAL_SENSOR_TYPE || callback == nullptr) {
            return HDF_ERR_INVALID_PARAM;
        }
        std::lock_guard<std::mutex> lock(operationMutex);
        if (stopped.load()) {
            return HDF_FAILURE;
        }
        std::lock_guard<std::mutex> callbacks(callbackMutex);
        auto &client = clients[id];
        client.callback = callback;
        client.asynchronous = asynchronous;
        return HDF_SUCCESS;
    }

    int32_t Unregister(int32_t group, const sptr<ISensorCallback> &callback, uint64_t id)
    {
        if (group != HDF_TRADITIONAL_SENSOR_TYPE || callback == nullptr) {
            return HDF_ERR_INVALID_PARAM;
        }
        std::lock_guard<std::mutex> lock(operationMutex);
        {
            std::lock_guard<std::mutex> callbacks(callbackMutex);
            auto found = clients.find(id);
            if (found == clients.end()) {
                return HDF_ERR_INVALID_OBJECT;
            }
            if (found->second.callback != callback) {
                if (!found->second.callback->IsProxy() || !callback->IsProxy()) {
                    return HDF_ERR_INVALID_OBJECT;
                }
                // 按底层回调对象识别不同IPC代理的同一订阅
                auto registeredObject = hdi_objcast<ISensorCallback>(found->second.callback);
                auto requestedObject = hdi_objcast<ISensorCallback>(callback);
                if (registeredObject == nullptr || registeredObject != requestedObject) {
                    return HDF_ERR_INVALID_OBJECT;
                }
            }
            clients.erase(found);
        }
        int32_t result = HDF_SUCCESS;
        for (auto &stream : streams) {
            const float previousRate = stream.rate;
            const bool previouslyRunning = stream.running;
            stream.intervals.erase(id);
            if (stream.enabled.erase(id) && Apply(stream) != HDF_SUCCESS) {
                result = HDF_FAILURE;
                if (previouslyRunning && previousRate > 0.0f && !stream.enabled.empty()) {
                    // 降频失败时恢复原物理速率，保留其余订阅
                    SscBackendConfig config{previousRate};
                    stream.lastError.store(SSC_OK);
                    int32_t restored = SscBackendStart(stream.backend, &config, OnSample, OnError, &stream);
                    stream.running = restored == SSC_OK;
                    stream.rate = stream.running ? previousRate : 0.0f;
                    if (restored != SSC_OK) {
                        stream.lastError.store(restored);
                    }
                }
            }
        }
        return result;
    }
};

SensorInterfaceService::SensorInterfaceService() : impl_(std::make_unique<Impl>()) {}
SensorInterfaceService::~SensorInterfaceService() = default;

int32_t SensorInterfaceService::Shutdown()
{
    std::lock_guard<std::mutex> lock(impl_->operationMutex);
    impl_->stopped.store(true);
    {
        std::lock_guard<std::mutex> callbacks(impl_->callbackMutex);
        impl_->clients.clear();
    }
    int32_t result = HDF_SUCCESS;
    // 服务退出前先停止全部真实订阅，再释放注册对象
    for (auto &stream : impl_->streams) {
        stream.enabled.clear();
        if (stream.backend != nullptr && SscBackendStop(stream.backend) != SSC_OK) {
            result = HDF_FAILURE;
        }
        stream.running = false;
    }
    return result;
}

int32_t SensorInterfaceService::GetAllSensorInfo(std::vector<HdfSensorInformation> &info)
{
    std::lock_guard<std::mutex> lock(impl_->operationMutex);
    info.clear();
    for (auto &stream : impl_->streams) {
        if (impl_->Discover(stream) != HDF_SUCCESS) {
            continue;
        }
        const auto &native = stream.info;
        uint32_t required = SSC_INFO_SELECTED_RANGE | SSC_INFO_SELECTED_RESOLUTION | SSC_INFO_RATES;
        if ((native.present & required) != required || native.rate_count == 0) {
            // 元数据不完整时允许下一次重新发现
            stream.discovered = false;
            continue;
        }
        auto rates = std::minmax_element(native.rates_hz, native.rates_hz + native.rate_count);
        HdfSensorInformation sensor{};
        sensor.deviceSensorInfo = Identity(stream.kind);
        sensor.sensorName = native.name;
        sensor.vendorName = native.vendor;
        sensor.firmwareVersion = std::to_string(native.version);
        sensor.maxRange = std::max(std::fabs(native.selected_range.minimum), std::fabs(native.selected_range.maximum));
        sensor.accuracy = native.selected_resolution;
        // 供体SensorService直接按纳秒接收HDI采样间隔
        sensor.minDelay = static_cast<int64_t>(1000000000.0 / *rates.second);
        sensor.maxDelay = static_cast<int64_t>(1000000000.0 / *rates.first);
        info.push_back(std::move(sensor));
    }
    return info.empty() ? HDF_FAILURE : HDF_SUCCESS;
}

int32_t SensorInterfaceService::GetDeviceSensorInfo(int32_t deviceId, std::vector<HdfSensorInformation> &info)
{
    if (deviceId != LOCAL_DEVICE) {
        info.clear();
        return HDF_ERR_INVALID_PARAM;
    }
    return GetAllSensorInfo(info);
}

int32_t SensorInterfaceService::Enable(const DeviceSensorInfo &info)
{
    return impl_->Enable(info, LEGACY_CLIENT, true);
}

int32_t SensorInterfaceService::Disable(const DeviceSensorInfo &info)
{
    return impl_->Enable(info, LEGACY_CLIENT, false);
}

int32_t SensorInterfaceService::EnableWithCallbackId(const DeviceSensorInfo &info, uint32_t id)
{
    return impl_->Enable(info, id, true);
}

int32_t SensorInterfaceService::DisableWithCallbackId(const DeviceSensorInfo &info, uint32_t id)
{
    return impl_->Enable(info, id, false);
}

int32_t SensorInterfaceService::SetBatch(const DeviceSensorInfo &info, int64_t sampling, int64_t report)
{
    return impl_->Batch(info, LEGACY_CLIENT, sampling, report);
}

int32_t SensorInterfaceService::SetBatchWithCallbackId(const DeviceSensorInfo &info, uint32_t id, int64_t sampling, int64_t report)
{
    return impl_->Batch(info, id, sampling, report);
}

int32_t SensorInterfaceService::Register(int32_t group, const sptr<ISensorCallback> &callback)
{
    (void)group;
    (void)callback;
    return HDF_ERR_NOT_SUPPORT;
}

int32_t SensorInterfaceService::RegisterAsync(int32_t group, const sptr<ISensorCallback> &callback)
{
    return impl_->Register(group, callback, LEGACY_CLIENT, true);
}

int32_t SensorInterfaceService::RegisterWithCallbackId(int32_t group, const sptr<ISensorCallback> &callback, uint32_t id)
{
    return impl_->Register(group, callback, id, true);
}

int32_t SensorInterfaceService::Unregister(int32_t group, const sptr<ISensorCallback> &callback)
{
    return impl_->Unregister(group, callback, LEGACY_CLIENT);
}

int32_t SensorInterfaceService::UnregisterAsync(int32_t group, const sptr<ISensorCallback> &callback)
{
    return impl_->Unregister(group, callback, LEGACY_CLIENT);
}

int32_t SensorInterfaceService::UnregisterWithCallbackId(int32_t group, const sptr<ISensorCallback> &callback, uint32_t id)
{
    return impl_->Unregister(group, callback, id);
}

int32_t SensorInterfaceService::SetMode(const DeviceSensorInfo &info, int32_t mode)
{
    return impl_->Find(info) != nullptr && (mode == 0 || mode == 1) ? HDF_SUCCESS : HDF_ERR_NOT_SUPPORT;
}

int32_t SensorInterfaceService::SetOption(const DeviceSensorInfo &info, uint32_t option)
{
    return impl_->Find(info) != nullptr && option == 0 ? HDF_SUCCESS : HDF_ERR_NOT_SUPPORT;
}

int32_t SensorInterfaceService::ReadData(const DeviceSensorInfo &, std::vector<HdfSensorEvents> &events)
{
    events.clear();
    return HDF_ERR_NOT_SUPPORT;
}

int32_t SensorInterfaceService::SetSdcSensor(const DeviceSensorInfo &, bool, int32_t)
{
    return HDF_ERR_NOT_SUPPORT;
}

int32_t SensorInterfaceService::GetSdcSensorInfo(std::vector<SdcSensorInfo> &info)
{
    info.clear();
    return HDF_ERR_NOT_SUPPORT;
}
int32_t SensorInterfaceService::RegSensorPlugCallBack(const sptr<ISensorPlugCallback> &)
{
    return HDF_ERR_NOT_SUPPORT;
}

int32_t SensorInterfaceService::UnRegSensorPlugCallBack(const sptr<ISensorPlugCallback> &)
{
    return HDF_ERR_NOT_SUPPORT;
}

extern "C" __attribute__((visibility("default"))) ISensorInterface *SensorInterfaceImplGetInstance()
{
    return new (std::nothrow) SensorInterfaceService();
}

extern "C" __attribute__((visibility("default"))) int32_t SensorInterfaceImplStopAll(ISensorInterface *service)
{
    return service == nullptr ? HDF_ERR_INVALID_PARAM : static_cast<SensorInterfaceService *>(service)->Shutdown();
}
}
