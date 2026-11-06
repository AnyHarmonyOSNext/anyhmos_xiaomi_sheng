#ifndef SSC_BACKEND_H
#define SSC_BACKEND_H

#include <stdint.h>

#ifdef __cplusplus
extern "C" {
#endif

typedef struct SscBackend SscBackend;

enum SscSensorKind {
    SSC_ACCEL = 1,
    SSC_GYRO = 2,
};

enum SscResult {
    SSC_OK = 0,
    SSC_INVALID = -1,
    SSC_SYSTEM_ERROR = -2,
    SSC_NO_SERVICE = -3,
    SSC_PROTOCOL_ERROR = -4,
    SSC_REMOTE_ERROR = -5,
    SSC_TIMEOUT = -6,
    SSC_NO_SENSOR = -7,
    SSC_NOT_AVAILABLE = -8,
    SSC_BUSY = -9,
    SSC_CALLBACK_REENTRY = -10,
    SSC_STOPPED = -11,
};

enum SscBackendState {
    SSC_IDLE = 0,
    SSC_STARTING = 1,
    SSC_RUNNING = 2,
    SSC_STOPPING = 3,
    SSC_STOPPED_STATE = 4,
    SSC_FAILED = 5,
};

enum SscStage {
    SSC_LOOKUP = 1,
    SSC_SUID = 2,
    SSC_ATTR = 3,
    SSC_CONFIG = 4,
    SSC_STREAM = 5,
    SSC_DISABLE = 6,
};

struct SscBackendError {
    int32_t result;
    int32_t system_errno;
    uint32_t stage;
    uint16_t qmi_result;
    uint16_t qmi_error;
    uint32_t sns_result;
    uint64_t sensor_error;
};

/* 数值、状态和DSP时间戳保持原值；接收时间为报文级单调时钟 */
struct SscRawSample {
    uint32_t kind;
    float values[3];
    uint64_t status;
    uint64_t timestamp_ticks;
    uint64_t arrival_mono_ns;
};

struct SscBackendConfig {
    float requested_rate_hz;
};

enum SscInfoField {
    SSC_INFO_NAME = 1u << 0,
    SSC_INFO_VENDOR = 1u << 1,
    SSC_INFO_AVAILABLE = 1u << 2,
    SSC_INFO_VERSION = 1u << 3,
    SSC_INFO_RATES = 1u << 4,
    SSC_INFO_RESOLUTIONS = 1u << 5,
    SSC_INFO_ACTIVE_CURRENT = 1u << 6,
    SSC_INFO_SLEEP_CURRENT = 1u << 7,
    SSC_INFO_RANGES = 1u << 8,
    SSC_INFO_OP_MODES = 1u << 9,
    SSC_INFO_SELECTED_RESOLUTION = 1u << 10,
    SSC_INFO_SELECTED_RANGE = 1u << 11,
};

struct SscRange { float minimum, maximum; };

/* present只标记实际取得的属性；电流保留uA，不推算未知功率 */
struct SscSensorInfo {
    uint32_t kind, present, truncated;
    uint32_t available, type_matches;
    char name[128], vendor[128];
    uint64_t version;
    uint32_t rate_count, resolution_count, range_count;
    float rates_hz[32], resolutions[32];
    struct SscRange ranges[32];
    uint32_t active_current_count, op_mode_count;
    int64_t active_current_ua[16], sleep_current_ua;
    char op_modes[16][32];
    float selected_resolution;
    struct SscRange selected_range;
};

/* 参数仅在回调期间有效；回调应及时返回，不在回调内调用生命周期接口 */
typedef void (*SscSampleCallback)(const struct SscRawSample *sample, void *context);
typedef void (*SscErrorCallback)(const struct SscBackendError *error, void *context);

int32_t SscBackendCreate(uint32_t kind, SscBackend **out);
/* 只读SUID和ATTR；数组或字符串超长通过truncated标记，不补造缺项 */
int32_t SscBackendDiscover(SscBackend *backend, struct SscSensorInfo *info);
int32_t SscBackendGetInfo(SscBackend *backend, struct SscSensorInfo *info);
/* 成功需收到原配置ACK和首个真实样本，失败时回收该次worker */
int32_t SscBackendStart(SscBackend *backend, const struct SscBackendConfig *config,
    SscSampleCallback on_sample, SscErrorCallback on_error, void *context);
/* 撤销本客户端请求并join；成功返回后不再触发该次回调 */
int32_t SscBackendStop(SscBackend *backend);
/* 调用方应独占句柄的销毁；返回成功表示本地资源已回收 */
int32_t SscBackendDestroy(SscBackend *backend);
int32_t SscBackendGetState(SscBackend *backend, uint32_t *state,
    struct SscBackendError *last_error);

#ifdef __cplusplus
}
#endif
#endif
