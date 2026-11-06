#ifndef SSC_WIRE_H
#define SSC_WIRE_H

#include <stdbool.h>
#include <stddef.h>
#include <stdint.h>
#include <string.h>
#include "ssc_backend.h"
#ifdef SSC_ATTR_DIAGNOSTIC
#include <stdio.h>
#endif

/* 沿用已验证的SSC编解码，报文内样本使用独立有界批次 */
struct View { const uint8_t *data; size_t size; };
struct Field { unsigned int id, wire; uint64_t value; struct View bytes; };
struct Buffer { uint8_t data[1000]; size_t size; bool failed; };
struct Suid { uint64_t low, high; };
struct Ack {
    uint16_t result, error;
    uint32_t sns_result;
    uint64_t client;
    bool has_sns_result, has_client;
};
struct Report { uint64_t client; struct View payload; };
struct Sample { float data[3]; uint64_t status, timestamp, arrival_ns; };
struct Sensor {
    const char *type;
    struct Suid suid;
    unsigned int suid_count, attr_count;
    bool suid_seen, attr_seen, type_seen, type_matches, available_seen, available;
    bool error_seen;
    uint64_t sns_error;
    size_t type_length, name_length;
    bool type_trailing_nul, type_raw_matches, name_seen, name_icm4x6xx;
    unsigned int type_class, sample_count, stored_samples, invalid_samples;
    uint64_t arrival_ns;
    struct Sample samples[32];
    struct SscSensorInfo *info;
};

static uint16_t Read16(const uint8_t *p)
{
    return (uint16_t)p[0] | (uint16_t)p[1] << 8;
}

static uint32_t Read32(const uint8_t *p)
{
    return (uint32_t)p[0] | (uint32_t)p[1] << 8 | (uint32_t)p[2] << 16 | (uint32_t)p[3] << 24;
}

static uint64_t Read64(const uint8_t *p)
{
    return (uint64_t)Read32(p) | (uint64_t)Read32(p + 4) << 32;
}

static void Write16(uint8_t *p, uint16_t value)
{
    p[0] = (uint8_t)value;
    p[1] = (uint8_t)(value >> 8);
}

static bool TakeVarint(struct View *view, uint64_t *value)
{
    *value = 0;
    for (unsigned int i = 0; i < 10; ++i) {
        if (view->size == 0) return false;
        const uint8_t byte = *view->data++;
        --view->size;
        if (i == 9 && byte > 1) return false;
        *value |= (uint64_t)(byte & 0x7f) << (7 * i);
        if (!(byte & 0x80)) return true;
    }
    return false;
}

/* 返回0为完整结束，-1为截断或不支持的线类型 */
static int NextField(struct View *view, struct Field *field)
{
    if (view->size == 0) return 0;
    uint64_t tag;
    if (!TakeVarint(view, &tag) || tag < 8 || (tag >> 3) > 0x1fffffff) return -1;
    *field = (struct Field){.id = (unsigned int)(tag >> 3), .wire = tag & 7};
    size_t length;
    if (field->wire == 0) return TakeVarint(view, &field->value) ? 1 : -1;
    if (field->wire == 1) length = 8;
    else if (field->wire == 5) length = 4;
    else if (field->wire == 2) {
        uint64_t count;
        if (!TakeVarint(view, &count) || count > view->size) return -1;
        length = (size_t)count;
    } else return -1;
    if (length > view->size) return -1;
    field->bytes = (struct View){view->data, length};
    if (field->wire == 1) field->value = Read64(view->data);
    if (field->wire == 5) field->value = Read32(view->data);
    view->data += length;
    view->size -= length;
    return 1;
}

static void Append(struct Buffer *out, const void *data, size_t size)
{
    if (size > sizeof(out->data) - out->size) { out->failed = true; return; }
    if (size != 0) memcpy(out->data + out->size, data, size);
    out->size += size;
}

static void PutVarint(struct Buffer *out, uint64_t value)
{
    do {
        uint8_t byte = value & 0x7f;
        value >>= 7;
        if (value != 0) byte |= 0x80;
        Append(out, &byte, 1);
    } while (value != 0);
}

static void PutFixed(struct Buffer *out, unsigned int id, uint64_t value, unsigned int width)
{
    PutVarint(out, (uint64_t)id * 8 + (width == 8 ? 1 : 5));
    for (unsigned int i = 0; i < width; ++i) {
        const uint8_t byte = (uint8_t)(value >> (i * 8));
        Append(out, &byte, 1);
    }
}

static void PutBytes(struct Buffer *out, unsigned int id, const void *data, size_t size)
{
    PutVarint(out, (uint64_t)id * 8 + 2);
    PutVarint(out, size);
    Append(out, data, size);
}

static bool SameSuid(struct Suid a, struct Suid b)
{
    return a.low == b.low && a.high == b.high;
}

static bool ParseSuid(struct View view, struct Suid *suid)
{
    struct Field field;
    unsigned int seen = 0;
    int next;
    while ((next = NextField(&view, &field)) > 0) {
        if (field.id != 1 && field.id != 2) continue;
        unsigned int bit = 1u << (field.id - 1);
        if (field.wire != 1 || (seen & bit)) return false;
        seen |= bit;
        if (field.id == 1) suid->low = field.value; else suid->high = field.value;
    }
    return next == 0 && seen == 3;
}

static size_t BuildSensorRequest(uint8_t *packet, uint16_t txn, struct Suid suid,
    uint32_t message, const uint8_t *payload, size_t payload_size)
{
    struct Buffer uid = {0}, standard = {0}, request = {0};
    const uint8_t suspend[] = {0x08, 1, 0x10, 0}; /* APSS，唤醒交付 */
    PutFixed(&uid, 1, suid.low, 8);
    PutFixed(&uid, 2, suid.high, 8);
    if (payload != NULL) PutBytes(&standard, 2, payload, payload_size);
    PutBytes(&request, 1, uid.data, uid.size);
    PutFixed(&request, 2, message, 4);
    PutBytes(&request, 3, suspend, sizeof(suspend));
    PutBytes(&request, 4, standard.data, standard.size);
    if (uid.failed || standard.failed || request.failed) return 0;
    packet[0] = 0;
    Write16(packet + 1, txn);
    Write16(packet + 3, 0x20);
    Write16(packet + 5, (uint16_t)(request.size + 5));
    packet[7] = 1;
    Write16(packet + 8, (uint16_t)(request.size + 2));
    Write16(packet + 10, (uint16_t)request.size);
    memcpy(packet + 12, request.data, request.size);
    return request.size + 12;
}

static size_t BuildRequest(uint8_t *packet, uint16_t txn, struct Suid suid, const char *type)
{
    struct Buffer body = {0};
    if (type == NULL) return BuildSensorRequest(packet, txn, suid, 1, NULL, 0);
    PutBytes(&body, 1, type, strlen(type));
    const uint8_t options[] = {0x10, 0, 0x18, 1};
    Append(&body, options, sizeof(options)); /* 不订阅更新，只查默认传感器 */
    if (body.failed) return 0;
    return BuildSensorRequest(packet, txn, suid, 512, body.data, body.size);
}

static size_t BuildStreamRequest(uint8_t *packet, struct Suid suid, bool disable, float rate_hz)
{
    uint8_t config[5] = {0x0d};
    uint32_t bits;
    memcpy(&bits, &rate_hz, sizeof(bits));
    for (unsigned int i = 0; i < 4; ++i) config[i + 1] = (uint8_t)(bits >> (i * 8));
    return BuildSensorRequest(packet, disable ? 4 : 3, suid, disable ? 10 : 513,
        disable ? NULL : config, disable ? 0 : sizeof(config));
}

/* QMI头已在调用方关联；此处只解已知TLV，不输出client ID */
static bool ParseAck(struct View view, struct Ack *ack)
{
    unsigned int seen = 0;
    *ack = (struct Ack){0};
    while (view.size != 0) {
        if (view.size < 3) return false;
        const uint8_t id = view.data[0];
        const size_t size = Read16(view.data + 1);
        view.data += 3; view.size -= 3;
        if (size > view.size) return false;
        if (id == 2) {
            if ((seen & 1) || size != 4) return false;
            seen |= 1;
            ack->result = Read16(view.data); ack->error = Read16(view.data + 2);
        } else if (id == 0x10) {
            if (ack->has_client || size != 8) return false;
            ack->has_client = true; ack->client = Read64(view.data);
        } else if (id == 0x11) {
            if (ack->has_sns_result || size != 4) return false;
            ack->has_sns_result = true; ack->sns_result = Read32(view.data);
        }
        view.data += size; view.size -= size;
    }
    return (seen & 1) != 0;
}

static bool ParseReport(struct View view, struct Report *report)
{
    unsigned int seen = 0;
    *report = (struct Report){0};
    while (view.size != 0) {
        if (view.size < 3) return false;
        const uint8_t id = view.data[0];
        const size_t size = Read16(view.data + 1);
        view.data += 3; view.size -= 3;
        if (size > view.size) return false;
        if (id == 1) {
            if ((seen & 1) || size != 8) return false;
            seen |= 1; report->client = Read64(view.data);
        } else if (id == 2) {
            if ((seen & 2) || size < 2 || Read16(view.data) != size - 2 || size > 1002) return false;
            seen |= 2; report->payload = (struct View){view.data + 2, size - 2};
        }
        view.data += size; view.size -= size;
    }
    return seen == 3;
}

static bool TextEquals(struct View value, const char *text)
{
    return value.size == strlen(text) && memcmp(value.data, text, value.size) == 0;
}

/* 属性字符串允许一个终止NUL，仍保留原长度及原始匹配结果 */
static struct View TrimTerminator(struct View value)
{
    if (value.size != 0 && value.data[value.size - 1] == 0) --value.size;
    return value;
}

static bool IsIcm4x6xx(struct View value)
{
    static const char chip[] = "icm4x6xx";
    value = TrimTerminator(value);
    for (size_t i = 0; i + sizeof(chip) - 1 <= value.size; ++i) {
        bool equal = true;
        for (size_t j = 0; j < sizeof(chip) - 1; ++j) {
            uint8_t byte = value.data[i + j];
            if (byte >= 'A' && byte <= 'Z') byte += 'a' - 'A';
            if (byte != (uint8_t)chip[j]) { equal = false; break; }
        }
        if (equal) return true;
    }
    return false;
}

static bool FloatValue(const struct Field *field, float *out)
{
    if (field->wire != 5) return false;
    uint32_t bits = (uint32_t)field->value;
    if ((bits & 0x7f800000) == 0x7f800000) return false;
    memcpy(out, &bits, 4);
    return true;
}

static void CopyText(char *out, size_t capacity, struct View text,
    struct SscSensorInfo *info, uint32_t flag)
{
    text = TrimTerminator(text);
    size_t size = text.size;
    if (size >= capacity) { size = capacity - 1; info->truncated |= flag; }
    memcpy(out, text.data, size);
    out[size] = 0;
}

static bool ParseFloatArray(struct View value, float *out, size_t capacity, uint32_t *count)
{
    struct Field field;
    int next;
    *count = 0;
    while ((next = NextField(&value, &field)) > 0) {
        if (field.id != 1) continue;
        if (field.wire != 2) return false;
        struct View item = field.bytes;
        struct Field data;
        bool found = false;
        int inner;
        while ((inner = NextField(&item, &data)) > 0) {
            if (data.id != 3) continue;
            float number;
            if (found || !FloatValue(&data, &number)) return false;
            found = true;
            if (*count < capacity) out[*count] = number;
            ++*count;
        }
        if (inner < 0 || !found) return false;
    }
    return next == 0;
}

static bool ParseInfoAttribute(uint64_t id, struct View value, struct SscSensorInfo *info)
{
    if (id == 24) {
        float values[2];
        uint32_t count;
        if (ParseFloatArray(value, values, 2, &count) && count == 2) {
            info->selected_range = (struct SscRange){values[0], values[1]};
        } else {
            /* 原stock将选定量程编码为单个range subtype */
            struct SscSensorInfo nested = {0};
            if (!ParseInfoAttribute(11, value, &nested) || nested.range_count != 1 || nested.truncated) return false;
            info->selected_range = nested.ranges[0];
        }
        info->present |= SSC_INFO_SELECTED_RANGE;
        return true;
    }
    if (id == 6 || id == 7 || id == 23) {
        float values[32];
        uint32_t count;
        if (!ParseFloatArray(value, values, 32, &count)) return false;
        uint32_t flag = id == 6 ? SSC_INFO_RATES : id == 7 ? SSC_INFO_RESOLUTIONS : SSC_INFO_SELECTED_RESOLUTION;
        if (count == 0) return true;
        if (count > 32) info->truncated |= flag;
        uint32_t stored = count < 32 ? count : 32;
        if (id == 6) { info->rate_count = stored; memcpy(info->rates_hz, values, stored * 4); }
        if (id == 7) { info->resolution_count = stored; memcpy(info->resolutions, values, stored * 4); }
        if (id == 23) { if (count != 1) return false; info->selected_resolution = values[0]; }
        info->present |= flag;
        return true;
    }
    struct Field field;
    int next;
    uint32_t count = 0;
    while ((next = NextField(&value, &field)) > 0) {
        if (field.id != 1) continue;
        if (field.wire != 2) return false;
        struct View item = field.bytes;
        struct Field data;
        int inner;
        while ((inner = NextField(&item, &data)) > 0) {
            if ((id == 0 || id == 1 || id == 12) && data.id == 2) {
                if (data.wire != 2) return false;
                uint32_t flag = id == 0 ? SSC_INFO_NAME : id == 1 ? SSC_INFO_VENDOR : SSC_INFO_OP_MODES;
                if (id == 0) CopyText(info->name, sizeof(info->name), data.bytes, info, flag);
                if (id == 1) CopyText(info->vendor, sizeof(info->vendor), data.bytes, info, flag);
                if (id == 12) {
                    if (count < 16) CopyText(info->op_modes[count], sizeof(info->op_modes[0]), data.bytes, info, flag);
                    else info->truncated |= flag;
                }
                ++count; info->present |= flag;
            } else if ((id == 4 || id == 9 || id == 10) && data.id == 4) {
                if (data.wire != 1) return false;
                int64_t number;
                memcpy(&number, &data.value, 8);
                if (id == 4) { info->version = data.value; info->present |= SSC_INFO_VERSION; }
                if (id == 10) { info->sleep_current_ua = number; info->present |= SSC_INFO_SLEEP_CURRENT; }
                if (id == 9) {
                    if (count < 16) info->active_current_ua[count] = number;
                    else info->truncated |= SSC_INFO_ACTIVE_CURRENT;
                    info->present |= SSC_INFO_ACTIVE_CURRENT;
                }
                ++count;
            } else if (id == 3 && data.id == 5) {
                if (data.wire != 0 || data.value > 1) return false;
                info->available = (uint32_t)data.value; info->present |= SSC_INFO_AVAILABLE;
            } else if (id == 11 && data.id == 1) {
                if (data.wire != 2) return false;
                float values[2];
                uint32_t numbers;
                if (!ParseFloatArray(data.bytes, values, 2, &numbers) || numbers != 2) return false;
                if (count < 32) info->ranges[count] = (struct SscRange){values[0], values[1]};
                else info->truncated |= SSC_INFO_RANGES;
                ++count; info->present |= SSC_INFO_RANGES;
            }
        }
        if (inner < 0) return false;
    }
    if (id == 9) info->active_current_count = count < 16 ? count : 16;
    if (id == 11) info->range_count = count < 32 ? count : 32;
    if (id == 12) info->op_mode_count = count < 16 ? count : 16;
    return next == 0;
}

#ifdef SSC_ATTR_DIAGNOSTIC
/* 只记录属性结构枚举，不输出属性文本或SUID */
static void AttributeDiagnostic(uint64_t id, struct View value, bool parsed)
{
    unsigned int count = 0, mask = 0;
    struct Field field;
    int next;
    while ((next = NextField(&value, &field)) > 0) {
        if (field.id != 1 || field.wire != 2) continue;
        ++count;
        struct View item = field.bytes;
        struct Field data;
        while (NextField(&item, &data) > 0) {
            if (data.id <= 5) mask |= 1u << data.id;
        }
    }
    fprintf(stderr, "SSC_ATTR_DIAGNOSTIC id=%llu kind_mask=%u count=%u parsecode=%u\n",
        (unsigned long long)id, mask, count, parsed ? 0 : 1);
}
#endif

static bool ParseSuidEvent(struct View view, struct Sensor *sensor)
{
    struct Field field;
    bool type_seen = false, type_matches = false;
    unsigned int count = 0;
    struct Suid chosen = {0};
    int next;
    while ((next = NextField(&view, &field)) > 0) {
        if (field.id == 1) {
            if (type_seen || field.wire != 2) return false;
            type_seen = true; type_matches = TextEquals(field.bytes, sensor->type);
        } else if (field.id == 2) {
            if (field.wire != 2 || !ParseSuid(field.bytes, &chosen)) return false;
            ++count;
        }
    }
    if (next < 0 || !type_seen) return false;
    if (type_matches) {
        sensor->suid_seen = true; sensor->suid_count = count; sensor->suid = chosen;
    }
    return true;
}

static bool ParseAttribute(struct View view, struct Sensor *sensor)
{
    struct Field field;
    bool id_seen = false, value_seen = false;
    uint64_t id = 0;
    struct View value = {0};
    int next;
    while ((next = NextField(&view, &field)) > 0) {
        if (field.id == 1) {
            if (id_seen || field.wire != 0) return false;
            id_seen = true; id = field.value;
        } else if (field.id == 2) {
            if (value_seen || field.wire != 2) return false;
            value_seen = true; value = field.bytes;
        }
    }
    if (next < 0 || !id_seen || !value_seen) return false;
    if (sensor->info != NULL) {
        bool parsed = ParseInfoAttribute(id, value, sensor->info);
#ifdef SSC_ATTR_DIAGNOSTIC
        AttributeDiagnostic(id, value, parsed);
#endif
        if (!parsed) return false;
    }
    ++sensor->attr_count;
    if (id != 0 && id != 2 && id != 3) return true;
    while ((next = NextField(&value, &field)) > 0) {
        if (field.id != 1) continue;
        if (field.wire != 2) return false;
        struct View item = field.bytes;
        struct Field data;
        int inner;
        while ((inner = NextField(&item, &data)) > 0) {
            if (id == 0 && data.id == 2) {
                if (data.wire != 2) return false;
                sensor->name_seen = true; sensor->name_length = data.bytes.size;
                sensor->name_icm4x6xx = IsIcm4x6xx(data.bytes);
            } else if (id == 2 && data.id == 2) {
                if (data.wire != 2) return false;
                sensor->type_seen = true;
                sensor->type_length = data.bytes.size;
                sensor->type_trailing_nul = data.bytes.size != 0 && data.bytes.data[data.bytes.size - 1] == 0;
                sensor->type_raw_matches = TextEquals(data.bytes, sensor->type);
                struct View normalized = TrimTerminator(data.bytes);
                sensor->type_matches = TextEquals(normalized, sensor->type);
                sensor->type_class = TextEquals(normalized, "accel") ? 1 : TextEquals(normalized, "gyro") ? 2 : 0;
            } else if (id == 3 && data.id == 5) {
                if (data.wire != 0 || data.value > 1) return false;
                sensor->available_seen = true; sensor->available = data.value != 0;
            }
        }
        if (inner < 0) return false;
    }
    return next == 0;
}

static bool ParseSample(struct View payload, uint64_t timestamp, struct Sensor *sensor)
{
    _Static_assert(sizeof(float) == 4, "float32 ABI");
    struct Field field;
    struct Sample sample = {.timestamp = timestamp, .arrival_ns = sensor->arrival_ns};
    unsigned int count = 0;
    bool status_seen = false, finite = true;
    int next;
    while ((next = NextField(&payload, &field)) > 0) {
        if (field.id == 1) {
            struct View floats = field.bytes;
            if (field.wire != 5 && field.wire != 2) return false;
            if (floats.size % 4 != 0) return false;
            while (floats.size != 0) {
                if (count >= 3) return false;
                uint32_t bits = Read32(floats.data);
                if ((bits & 0x7f800000) == 0x7f800000) finite = false;
                memcpy(&sample.data[count++], &bits, 4);
                floats.data += 4; floats.size -= 4;
            }
        } else if (field.id == 2) {
            if (status_seen || field.wire != 0) return false;
            status_seen = true; sample.status = field.value;
        }
    }
    if (next < 0 || count != 3 || !status_seen) return false;
    ++sensor->sample_count;
    if (!finite) ++sensor->invalid_samples;
    else {
        if (sensor->stored_samples >= 32) return false;
        sensor->samples[sensor->stored_samples++] = sample;
    }
    return true;
}

static bool ParsePayload(uint32_t msg, struct View payload, struct Sensor *sensor)
{
    if (msg == 768) return ParseSuidEvent(payload, sensor);
    struct Field field;
    int next;
    while ((next = NextField(&payload, &field)) > 0) {
        if (msg == 128 && field.id == 1) {
            if (field.wire != 2 || !ParseAttribute(field.bytes, sensor)) return false;
            sensor->attr_seen = true;
        } else if (msg == 130 && field.id == 1) {
            if (field.wire != 0 || sensor->error_seen) return false;
            sensor->error_seen = true; sensor->sns_error = field.value;
        }
    }
    return next == 0;
}

static bool ParseEvents(struct View view, unsigned int mode, struct Sensor *sensor)
{
    struct Field field;
    struct Suid uid = {0};
    bool uid_seen = false;
    struct View events = view;
    int next;
    while ((next = NextField(&view, &field)) > 0) {
        if (field.id == 1) {
            if (uid_seen || field.wire != 2 || !ParseSuid(field.bytes, &uid)) return false;
            uid_seen = true;
        }
    }
    const struct Suid lookup = {UINT64_C(0xabababababababab), UINT64_C(0xabababababababab)};
    if (next < 0 || !uid_seen) return false;
    if (!SameSuid(uid, mode != 0 ? sensor->suid : lookup)) return true;
    while ((next = NextField(&events, &field)) > 0) {
        if (field.id != 2) continue;
        if (field.wire != 2) return false;
        struct View event = field.bytes, payload = {0};
        unsigned int seen = 0;
        uint32_t msg = 0;
        uint64_t timestamp = 0;
        struct Field part;
        int inner;
        while ((inner = NextField(&event, &part)) > 0) {
            if (part.id < 1 || part.id > 3) continue;
            unsigned int bit = 1u << (part.id - 1);
            if (seen & bit) return false;
            seen |= bit;
            if (part.id == 1) { if (part.wire != 5) return false; msg = (uint32_t)part.value; }
            if (part.id == 2) { if (part.wire != 1) return false; timestamp = part.value; }
            if (part.id == 3) { if (part.wire != 2) return false; payload = part.bytes; }
        }
        if (inner < 0 || seen != 7) return false;
        if (mode == 2 && msg == 1025) {
            if (!ParseSample(payload, timestamp, sensor)) return false;
        } else if (((mode == 1 && (msg == 128 || msg == 130)) ||
             (mode == 0 && (msg == 768 || msg == 130)) ||
             (mode == 2 && msg == 130)) && !ParsePayload(msg, payload, sensor)) return false;
    }
    return next == 0;
}

#endif
