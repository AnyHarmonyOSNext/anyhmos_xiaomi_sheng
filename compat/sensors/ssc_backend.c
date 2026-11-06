#include "ssc_backend.h"
#include "ssc_wire.h"
#include "libqrtr.h"

#include <errno.h>
#include <fcntl.h>
#include <poll.h>
#include <pthread.h>
#include <stdlib.h>
#include <sys/socket.h>
#include <time.h>
#include <unistd.h>

enum { SERVICE = 400, VERSION = 1, WINDOW_MS = 3000, MAX_ENDPOINTS = 16 };
struct Endpoint { uint32_t node, port; bool active; };

struct SscBackend {
    pthread_mutex_t operation;
    pthread_mutex_t lock;
    pthread_cond_t changed;
    pthread_t worker;
    int wake[2];
    bool joinable, stop;
    uint32_t kind, state;
    float rate_hz;
    SscSampleCallback on_sample;
    SscErrorCallback on_error;
    void *context;
    struct SscBackendError error;
    struct SscSensorInfo info;
    bool info_valid;
};

static int64_t NowMs(void)
{
    struct timespec now;
    if (clock_gettime(CLOCK_MONOTONIC, &now)) return -1;
    return (int64_t)now.tv_sec * 1000 + now.tv_nsec / 1000000;
}

static int Failure(struct SscBackendError *error, int result, int system_errno)
{
    error->result = result;
    error->system_errno = system_errno;
    return result;
}

static bool StopRequested(SscBackend *backend)
{
    pthread_mutex_lock(&backend->lock);
    bool stop = backend->stop;
    pthread_mutex_unlock(&backend->lock);
    return stop;
}

static void RequestStop(SscBackend *backend)
{
    pthread_mutex_lock(&backend->lock);
    backend->stop = true;
    if (backend->state == SSC_STARTING || backend->state == SSC_RUNNING) backend->state = SSC_STOPPING;
    pthread_mutex_unlock(&backend->lock);
    const uint8_t byte = 1;
    /* pipe为非阻塞；已有唤醒字节时无需重复写入 */
    ssize_t written;
    do { written = write(backend->wake[1], &byte, 1); } while (written < 0 && errno == EINTR);
}

static int Receive(SscBackend *backend, int fd, int64_t deadline, bool stopping_allowed,
    uint8_t *data, size_t capacity, struct sockaddr_qrtr *source, size_t *size,
    struct SscBackendError *error)
{
    while (1) {
        if (!stopping_allowed && StopRequested(backend)) return SSC_STOPPED;
        const int64_t now = NowMs();
        if (now < 0) return Failure(error, SSC_SYSTEM_ERROR, errno);
        if (now >= deadline) return SSC_TIMEOUT;
        struct pollfd items[2] = {{.fd = fd, .events = POLLIN}, {.fd = backend->wake[0], .events = POLLIN}};
        int ready = poll(items, stopping_allowed ? 1 : 2, (int)(deadline - now));
        if (ready < 0) { if (errno == EINTR) continue; return Failure(error, SSC_SYSTEM_ERROR, errno); }
        if (!ready) continue;
        if (!stopping_allowed && items[1].revents) {
            if (StopRequested(backend)) return SSC_STOPPED;
            uint8_t drain[32];
            while (read(backend->wake[0], drain, sizeof(drain)) > 0) {}
        }
        if (items[0].revents & (POLLERR | POLLHUP | POLLNVAL)) return Failure(error, SSC_SYSTEM_ERROR, 0);
        if (!(items[0].revents & POLLIN)) continue;
        socklen_t source_size = sizeof(*source);
        ssize_t received = recvfrom(fd, data, capacity, MSG_TRUNC,
            (struct sockaddr *)source, &source_size);
        if (received < 0) {
            if (errno == EINTR || errno == EAGAIN || errno == EWOULDBLOCK) continue;
            return Failure(error, SSC_SYSTEM_ERROR, errno);
        }
        if (source_size != sizeof(*source) || source->sq_family != AF_QIPCRTR ||
            (size_t)received > capacity) return Failure(error, SSC_PROTOCOL_ERROR, 0);
        *size = (size_t)received;
        return SSC_OK;
    }
}

static int FindEndpoint(SscBackend *backend, int fd, struct Endpoint *chosen,
    struct SscBackendError *error)
{
    error->stage = SSC_LOOKUP;
    if (qrtr_new_lookup(fd, SERVICE, VERSION, 0)) return Failure(error, SSC_SYSTEM_ERROR, errno);
    struct Endpoint entries[MAX_ENDPOINTS] = {0};
    bool eof = false;
    unsigned int active = 0;
    int result = 0;
    const int64_t start = NowMs();
    if (start < 0) result = Failure(error, SSC_SYSTEM_ERROR, errno);
    while (!result && !eof) {
        uint8_t data[256];
        size_t size = 0;
        struct sockaddr_qrtr source = {0};
        result = Receive(backend, fd, start + WINDOW_MS, false, data, sizeof(data), &source, &size, error);
        if (result) break;
        struct qrtr_packet packet = {0};
        if (source.sq_port != QRTR_PORT_CTRL || qrtr_decode(&packet, data, size, &source)) continue;
        if (packet.type == QRTR_TYPE_NEW_SERVER && packet.service == 0 && packet.node == 0 &&
            packet.port == 0 && packet.version == 0 && packet.instance == 0) { eof = true; break; }
        if ((packet.type != QRTR_TYPE_NEW_SERVER && packet.type != QRTR_TYPE_DEL_SERVER) ||
            packet.service != SERVICE || packet.version != VERSION || packet.port == 0) continue;
        int empty = -1, found = -1;
        for (int i = 0; i < MAX_ENDPOINTS; ++i) {
            if (!entries[i].active) { if (empty < 0) empty = i; }
            else if (entries[i].node == packet.node && entries[i].port == packet.port) found = i;
        }
        if (packet.type == QRTR_TYPE_DEL_SERVER) {
            if (found >= 0) entries[found].active = false;
        } else if (found < 0) {
            if (empty < 0) { result = Failure(error, SSC_PROTOCOL_ERROR, 0); break; }
            entries[empty] = (struct Endpoint){packet.node, packet.port, true};
        }
    }
    if (qrtr_remove_lookup(fd, SERVICE, VERSION, 0) && !result) result = Failure(error, SSC_SYSTEM_ERROR, errno);
    if (result) return result;
    for (int i = 0; i < MAX_ENDPOINTS; ++i) {
        if (entries[i].active) { ++active; *chosen = entries[i]; }
    }
    if (!active) return Failure(error, SSC_NO_SERVICE, 0);
    return active == 1 ? SSC_OK : Failure(error, SSC_PROTOCOL_ERROR, 0);
}

static int AcceptAck(struct View body, bool *client_seen, uint64_t *client,
    struct SscBackendError *error)
{
    struct Ack ack;
    if (!ParseAck(body, &ack)) return Failure(error, SSC_PROTOCOL_ERROR, 0);
    error->qmi_result = ack.result;
    error->qmi_error = ack.error;
    error->sns_result = ack.has_sns_result ? ack.sns_result : 0;
    if (ack.result || ack.error || (ack.has_sns_result && ack.sns_result)) return Failure(error, SSC_REMOTE_ERROR, 0);
    if (ack.has_client) {
        if (*client_seen && *client != ack.client) return Failure(error, SSC_PROTOCOL_ERROR, 0);
        *client_seen = true; *client = ack.client;
    }
    return SSC_OK;
}

static int AcceptReport(struct View body, unsigned int mode, struct Sensor *sensor,
    bool *client_seen, uint64_t *client, struct SscBackendError *error)
{
    struct Report report;
    if (!ParseReport(body, &report) || (*client_seen && *client != report.client))
        return Failure(error, SSC_PROTOCOL_ERROR, 0);
    *client_seen = true; *client = report.client;
    struct Sensor candidate = *sensor;
    candidate.sample_count = candidate.stored_samples = candidate.invalid_samples = 0;
    candidate.error_seen = false;
    struct timespec arrival;
    if (clock_gettime(CLOCK_MONOTONIC, &arrival)) return Failure(error, SSC_SYSTEM_ERROR, errno);
    candidate.arrival_ns = (uint64_t)arrival.tv_sec * UINT64_C(1000000000) + arrival.tv_nsec;
    if (!ParseEvents(report.payload, mode, &candidate)) return Failure(error, SSC_PROTOCOL_ERROR, 0);
    if (candidate.error_seen && candidate.sns_error != 0) {
        error->sensor_error = candidate.sns_error;
        return Failure(error, SSC_REMOTE_ERROR, 0);
    }
    /* 跳过非有限样本，继续交付同批有效数据 */
    *sensor = candidate;
    return SSC_OK;
}

static int QueryPhase(SscBackend *backend, int fd, const struct Endpoint *endpoint,
    struct Sensor *sensor, bool attributes, bool *client_seen, uint64_t *client,
    struct SscBackendError *error)
{
    error->stage = attributes ? SSC_ATTR : SSC_SUID;
    const struct Suid lookup = {UINT64_C(0xabababababababab), UINT64_C(0xabababababababab)};
    const uint16_t txn = attributes ? 2 : 1;
    uint8_t request[1012];
    size_t request_size = BuildRequest(request, txn, attributes ? sensor->suid : lookup,
        attributes ? NULL : sensor->type);
    const int64_t start = NowMs();
    if (!request_size || start < 0) return Failure(error, SSC_SYSTEM_ERROR, start < 0 ? errno : 0);
    if (qrtr_sendto(fd, endpoint->node, endpoint->port, request, (unsigned int)request_size))
        return Failure(error, SSC_SYSTEM_ERROR, errno);
    bool ack_seen = false;
    while (1) {
        uint8_t data[2048];
        size_t size = 0;
        struct sockaddr_qrtr source = {0};
        int result = Receive(backend, fd, start + WINDOW_MS, false, data, sizeof(data), &source, &size, error);
        if (result) return Failure(error, result, error->system_errno);
        if (source.sq_node != endpoint->node || source.sq_port != endpoint->port) continue;
        if (size < 7 || Read16(data + 5) != size - 7) return Failure(error, SSC_PROTOCOL_ERROR, 0);
        struct View body = {data + 7, size - 7};
        if (data[0] == QMI_RESPONSE && Read16(data + 1) == txn && Read16(data + 3) == 0x20) {
            if (ack_seen) return Failure(error, SSC_PROTOCOL_ERROR, 0);
            result = AcceptAck(body, client_seen, client, error);
            if (result) return result;
            ack_seen = true;
        } else if (data[0] == QMI_INDICATION && Read16(data + 3) == 0x21) {
            result = AcceptReport(body, attributes ? 1 : 0, sensor, client_seen, client, error);
            if (result) return result;
        } else continue;
        if (ack_seen && (attributes ? sensor->attr_seen : sensor->suid_seen)) return SSC_OK;
    }
}

static void MarkRunning(SscBackend *backend)
{
    pthread_mutex_lock(&backend->lock);
    if (!backend->stop) backend->state = SSC_RUNNING;
    pthread_cond_broadcast(&backend->changed);
    pthread_mutex_unlock(&backend->lock);
}

static int RunStream(SscBackend *backend, int fd, const struct Endpoint *endpoint,
    struct Sensor *sensor, bool *client_seen, uint64_t *client,
    struct SscBackendError *error, bool *submitted)
{
    error->stage = SSC_CONFIG;
    uint8_t request[1012];
    size_t request_size = BuildStreamRequest(request, sensor->suid, false, backend->rate_hz);
    const int64_t start = NowMs();
    if (!request_size || start < 0) return Failure(error, SSC_SYSTEM_ERROR, start < 0 ? errno : 0);
    if (qrtr_sendto(fd, endpoint->node, endpoint->port, request, (unsigned int)request_size))
        return Failure(error, SSC_SYSTEM_ERROR, errno);
    *submitted = true;
    bool ack_seen = false, sample_seen = false, running = false, batch_ready = false;
    while (1) {
        if (StopRequested(backend)) return SSC_STOPPED;
        uint8_t data[2048];
        size_t size = 0;
        struct sockaddr_qrtr source = {0};
        int64_t now = NowMs();
        if (now < 0) return Failure(error, SSC_SYSTEM_ERROR, errno);
        int result = Receive(backend, fd, running ? now + 1000 : start + WINDOW_MS,
            false, data, sizeof(data), &source, &size, error);
        if (result == SSC_TIMEOUT && running) continue;
        if (result) return Failure(error, result, error->system_errno);
        if (source.sq_node != endpoint->node || source.sq_port != endpoint->port) continue;
        if (size < 7 || Read16(data + 5) != size - 7) return Failure(error, SSC_PROTOCOL_ERROR, 0);
        struct View body = {data + 7, size - 7};
        if (data[0] == QMI_RESPONSE && Read16(data + 1) == 3 && Read16(data + 3) == 0x20) {
            if (ack_seen) return Failure(error, SSC_PROTOCOL_ERROR, 0);
            result = AcceptAck(body, client_seen, client, error);
            if (result) return result;
            ack_seen = true;
        } else if (data[0] == QMI_INDICATION && Read16(data + 3) == 0x21) {
            result = AcceptReport(body, 2, sensor, client_seen, client, error);
            if (result) return result;
            if (sensor->stored_samples != 0) { sample_seen = true; batch_ready = true; }
        }
        /* 先发布真实就绪状态，避免启动调用与上层回调锁互等 */
        if (!running && ack_seen && sample_seen) {
            running = true;
            error->stage = SSC_STREAM;
            MarkRunning(backend);
        }
        if (running && batch_ready) {
            for (unsigned int i = 0; i < sensor->stored_samples; ++i) {
                if (StopRequested(backend)) return SSC_STOPPED;
                const struct Sample *sample = &sensor->samples[i];
                struct SscRawSample raw = {.kind = backend->kind,
                    .status = sample->status, .timestamp_ticks = sample->timestamp,
                    .arrival_mono_ns = sample->arrival_ns};
                memcpy(raw.values, sample->data, sizeof(raw.values));
                backend->on_sample(&raw, backend->context);
            }
            batch_ready = false;
        }
    }
}

static int Disable(SscBackend *backend, int fd, const struct Endpoint *endpoint,
    struct Sensor *sensor, bool *client_seen, uint64_t *client, struct SscBackendError *error)
{
    error->stage = SSC_DISABLE;
    uint8_t request[1012];
    size_t request_size = BuildStreamRequest(request, sensor->suid, true, backend->rate_hz);
    const int64_t start = NowMs();
    if (!request_size || start < 0) return Failure(error, SSC_SYSTEM_ERROR, start < 0 ? errno : 0);
    if (qrtr_sendto(fd, endpoint->node, endpoint->port, request, (unsigned int)request_size))
        return Failure(error, SSC_SYSTEM_ERROR, errno);
    while (1) {
        uint8_t data[2048];
        size_t size = 0;
        struct sockaddr_qrtr source = {0};
        int result = Receive(backend, fd, start + 1000, true, data, sizeof(data), &source, &size, error);
        if (result) return Failure(error, result, error->system_errno);
        if (source.sq_node != endpoint->node || source.sq_port != endpoint->port) continue;
        if (size < 7 || Read16(data + 5) != size - 7) return Failure(error, SSC_PROTOCOL_ERROR, 0);
        if (data[0] != QMI_RESPONSE || Read16(data + 1) != 4 || Read16(data + 3) != 0x20) continue;
        return AcceptAck((struct View){data + 7, size - 7}, client_seen, client, error);
    }
}

static void *Worker(void *argument)
{
    SscBackend *backend = argument;
    struct SscBackendError error = {0};
    struct Endpoint endpoint = {0};
    struct SscSensorInfo info = {.kind = backend->kind};
    struct Sensor sensor = {.type = backend->kind == SSC_ACCEL ? "accel" : "gyro", .info = &info};
    bool client_seen = false, submitted = false;
    uint64_t client = 0;
    int fd = socket(AF_QIPCRTR, SOCK_DGRAM | SOCK_CLOEXEC | SOCK_NONBLOCK, 0);
    int result = fd < 0 ? Failure(&error, SSC_SYSTEM_ERROR, errno) : SSC_OK;
    if (!result) result = FindEndpoint(backend, fd, &endpoint, &error);
    if (!result) result = QueryPhase(backend, fd, &endpoint, &sensor, false, &client_seen, &client, &error);
    if (!result && sensor.suid_count != 1) result = Failure(&error, SSC_NO_SENSOR, 0);
    if (!result) result = QueryPhase(backend, fd, &endpoint, &sensor, true, &client_seen, &client, &error);
    if (!result) {
        info.type_matches = sensor.type_seen && sensor.type_matches;
        pthread_mutex_lock(&backend->lock);
        backend->info = info; backend->info_valid = true;
        pthread_mutex_unlock(&backend->lock);
    }
    if (!result && (!sensor.type_seen || !sensor.type_matches || !sensor.available_seen || !sensor.available))
        result = Failure(&error, SSC_NOT_AVAILABLE, 0);
    if (!result) result = RunStream(backend, fd, &endpoint, &sensor, &client_seen, &client, &error, &submitted);
    /* 即使接收失败，也只撤销本socket已提交的请求 */
    if (submitted) {
        struct SscBackendError cleanup = {0};
        int disabled = Disable(backend, fd, &endpoint, &sensor, &client_seen, &client, &cleanup);
        if ((result == SSC_STOPPED || result == SSC_OK) && disabled) { result = disabled; error = cleanup; }
    }
    if (fd >= 0 && close(fd) && (result == SSC_STOPPED || result == SSC_OK)) result = Failure(&error, SSC_SYSTEM_ERROR, errno);
    bool failed = result != SSC_STOPPED && result != SSC_OK;
    if (failed && error.result == 0) error.result = result;
    pthread_mutex_lock(&backend->lock);
    backend->state = failed ? SSC_FAILED : SSC_STOPPED_STATE;
    backend->error = failed ? error : (struct SscBackendError){0};
    pthread_cond_broadcast(&backend->changed);
    pthread_mutex_unlock(&backend->lock);
    if (failed && backend->on_error) backend->on_error(&error, backend->context);
    return NULL;
}

static bool IsWorker(SscBackend *backend)
{
    pthread_mutex_lock(&backend->lock);
    bool own = backend->joinable && pthread_equal(pthread_self(), backend->worker);
    pthread_mutex_unlock(&backend->lock);
    return own;
}

static int JoinWorker(SscBackend *backend)
{
    if (!backend->joinable) return SSC_OK;
    int joined = pthread_join(backend->worker, NULL);
    if (joined) return SSC_SYSTEM_ERROR;
    pthread_mutex_lock(&backend->lock);
    backend->joinable = false;
    backend->on_sample = NULL; backend->on_error = NULL; backend->context = NULL;
    pthread_mutex_unlock(&backend->lock);
    return SSC_OK;
}

int32_t SscBackendCreate(uint32_t kind, SscBackend **out)
{
    if (out == NULL) return SSC_INVALID;
    *out = NULL;
    if (kind != SSC_ACCEL && kind != SSC_GYRO) return SSC_INVALID;
    SscBackend *backend = calloc(1, sizeof(*backend));
    if (backend == NULL) return SSC_SYSTEM_ERROR;
    backend->kind = kind;
    if (pthread_mutex_init(&backend->operation, NULL)) { free(backend); return SSC_SYSTEM_ERROR; }
    if (pthread_mutex_init(&backend->lock, NULL)) {
        pthread_mutex_destroy(&backend->operation); free(backend); return SSC_SYSTEM_ERROR;
    }
    pthread_condattr_t attr;
    int result = pthread_condattr_init(&attr);
    if (!result) {
        result = pthread_condattr_setclock(&attr, CLOCK_MONOTONIC);
        if (!result) result = pthread_cond_init(&backend->changed, &attr);
        pthread_condattr_destroy(&attr);
    }
    if (result || pipe2(backend->wake, O_CLOEXEC | O_NONBLOCK)) {
        if (!result) pthread_cond_destroy(&backend->changed);
        pthread_mutex_destroy(&backend->lock); pthread_mutex_destroy(&backend->operation);
        free(backend); return SSC_SYSTEM_ERROR;
    }
    *out = backend;
    return SSC_OK;
}

int32_t SscBackendStart(SscBackend *backend, const struct SscBackendConfig *config,
    SscSampleCallback on_sample, SscErrorCallback on_error, void *context)
{
    if (backend == NULL || config == NULL || on_sample == NULL) return SSC_INVALID;
    uint32_t rate_bits;
    memcpy(&rate_bits, &config->requested_rate_hz, 4);
    if (!(config->requested_rate_hz > 0.0f) || (rate_bits & 0x7f800000) == 0x7f800000) return SSC_INVALID;
    if (IsWorker(backend)) return SSC_CALLBACK_REENTRY;
    pthread_mutex_lock(&backend->operation);
    pthread_mutex_lock(&backend->lock);
    if (backend->joinable) {
        pthread_mutex_unlock(&backend->lock); pthread_mutex_unlock(&backend->operation); return SSC_BUSY;
    }
    uint8_t drain[32];
    while (read(backend->wake[0], drain, sizeof(drain)) > 0) {}
    backend->stop = false; backend->state = SSC_STARTING;
    backend->info_valid = false;
    backend->error = (struct SscBackendError){0};
    backend->rate_hz = config->requested_rate_hz;
    backend->on_sample = on_sample; backend->on_error = on_error; backend->context = context;
    int created = pthread_create(&backend->worker, NULL, Worker, backend);
    if (created) {
        backend->state = SSC_FAILED;
        backend->error = (struct SscBackendError){.result = SSC_SYSTEM_ERROR, .system_errno = created};
        pthread_mutex_unlock(&backend->lock); pthread_mutex_unlock(&backend->operation); return SSC_SYSTEM_ERROR;
    }
    backend->joinable = true;
    struct timespec deadline;
    int wait_result = clock_gettime(CLOCK_MONOTONIC, &deadline);
    if (!wait_result) {
        deadline.tv_sec += 15;
        while (backend->state == SSC_STARTING || backend->state == SSC_STOPPING) {
            wait_result = pthread_cond_timedwait(&backend->changed, &backend->lock, &deadline);
            if (wait_result) break;
        }
    }
    int result = backend->state == SSC_RUNNING ? SSC_OK : backend->error.result;
    if (!result && backend->state != SSC_RUNNING) result = SSC_STOPPED;
    pthread_mutex_unlock(&backend->lock);
    if (wait_result) { result = wait_result == ETIMEDOUT ? SSC_TIMEOUT : SSC_SYSTEM_ERROR; RequestStop(backend); }
    if (result != SSC_OK) {
        int joined = JoinWorker(backend);
        if (joined) result = joined;
    }
    pthread_mutex_unlock(&backend->operation);
    return result;
}

int32_t SscBackendStop(SscBackend *backend)
{
    if (backend == NULL) return SSC_INVALID;
    if (IsWorker(backend)) return SSC_CALLBACK_REENTRY;
    RequestStop(backend);
    pthread_mutex_lock(&backend->operation);
    /* 与并发Start串行后再次置位，防止新一轮启动清掉旧唤醒 */
    RequestStop(backend);
    int result = JoinWorker(backend);
    pthread_mutex_lock(&backend->lock);
    if (!result && backend->state == SSC_FAILED) result = backend->error.result;
    if (!result) backend->state = SSC_STOPPED_STATE;
    pthread_mutex_unlock(&backend->lock);
    pthread_mutex_unlock(&backend->operation);
    return result;
}

int32_t SscBackendDestroy(SscBackend *backend)
{
    if (backend == NULL) return SSC_INVALID;
    if (IsWorker(backend)) return SSC_CALLBACK_REENTRY;
    int result = SscBackendStop(backend);
    if (backend->joinable) return result;
    close(backend->wake[0]); close(backend->wake[1]);
    pthread_cond_destroy(&backend->changed);
    pthread_mutex_destroy(&backend->lock); pthread_mutex_destroy(&backend->operation);
    free(backend);
    return SSC_OK;
}

int32_t SscBackendDiscover(SscBackend *backend, struct SscSensorInfo *out)
{
    if (backend == NULL || out == NULL) return SSC_INVALID;
    *out = (struct SscSensorInfo){0};
    if (IsWorker(backend)) return SSC_CALLBACK_REENTRY;
    pthread_mutex_lock(&backend->operation);
    pthread_mutex_lock(&backend->lock);
    if (backend->joinable) {
        pthread_mutex_unlock(&backend->lock); pthread_mutex_unlock(&backend->operation); return SSC_BUSY;
    }
    backend->stop = false; backend->info_valid = false;
    uint8_t drain[32];
    while (read(backend->wake[0], drain, sizeof(drain)) > 0) {}
    pthread_mutex_unlock(&backend->lock);
    struct SscSensorInfo info = {.kind = backend->kind};
    struct Sensor sensor = {.type = backend->kind == SSC_ACCEL ? "accel" : "gyro", .info = &info};
    struct SscBackendError error = {0};
    struct Endpoint endpoint = {0};
    bool client_seen = false;
    uint64_t client = 0;
    int fd = socket(AF_QIPCRTR, SOCK_DGRAM | SOCK_CLOEXEC | SOCK_NONBLOCK, 0);
    int result = fd < 0 ? Failure(&error, SSC_SYSTEM_ERROR, errno) : SSC_OK;
    if (!result) result = FindEndpoint(backend, fd, &endpoint, &error);
    if (!result) result = QueryPhase(backend, fd, &endpoint, &sensor, false, &client_seen, &client, &error);
    if (!result && sensor.suid_count != 1) result = Failure(&error, SSC_NO_SENSOR, 0);
    if (!result) result = QueryPhase(backend, fd, &endpoint, &sensor, true, &client_seen, &client, &error);
    if (fd >= 0 && close(fd) && !result) result = Failure(&error, SSC_SYSTEM_ERROR, errno);
    pthread_mutex_lock(&backend->lock);
    if (!result) {
        info.type_matches = sensor.type_seen && sensor.type_matches;
        backend->info = info; backend->info_valid = true;
        *out = info;
    }
    backend->error = error;
    pthread_mutex_unlock(&backend->lock);
    pthread_mutex_unlock(&backend->operation);
    return result;
}

int32_t SscBackendGetInfo(SscBackend *backend, struct SscSensorInfo *out)
{
    if (backend == NULL || out == NULL) return SSC_INVALID;
    pthread_mutex_lock(&backend->lock);
    int result = backend->info_valid ? SSC_OK : SSC_NOT_AVAILABLE;
    *out = backend->info_valid ? backend->info : (struct SscSensorInfo){0};
    pthread_mutex_unlock(&backend->lock);
    return result;
}

int32_t SscBackendGetState(SscBackend *backend, uint32_t *state, struct SscBackendError *last_error)
{
    if (backend == NULL || state == NULL) return SSC_INVALID;
    pthread_mutex_lock(&backend->lock);
    *state = backend->state;
    if (last_error != NULL) *last_error = backend->error;
    pthread_mutex_unlock(&backend->lock);
    return SSC_OK;
}
