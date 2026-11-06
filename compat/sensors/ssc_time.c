#include "ssc_time.h"

#include <errno.h>
#include <limits.h>
#include <time.h>

#define NS_PER_SECOND UINT64_C(1000000000)
#define EVENT_REFRESH_NS INT64_C(60000000000)
#define SAMPLE_SPAN_NS UINT64_C(10000)
#define SAMPLE_ATTEMPTS 20

static uint64_t ReadFrequency(void)
{
    uint64_t value;
    __asm__ volatile("mrs %0, cntfrq_el0" : "=r"(value));
    return value;
}

static uint64_t ReadCounter(void)
{
    uint64_t value;
    __asm__ volatile("isb\n\tmrs %0, cntvct_el0" : "=r"(value) : : "memory");
    return value;
}

static int ReadBootTime(int64_t *value)
{
    struct timespec now;
    if (clock_gettime(CLOCK_BOOTTIME, &now)) return -errno;
    if (now.tv_sec < 0 || (uint64_t)now.tv_sec > INT64_MAX / NS_PER_SECOND)
        return -ERANGE;
    uint64_t ns = (uint64_t)now.tv_sec * NS_PER_SECOND + (uint64_t)now.tv_nsec;
    if (ns > INT64_MAX) return -ERANGE;
    *value = (int64_t)ns;
    return 0;
}

/* 按原厂实际计数频率换算，保留整数纳秒精度 */
static int CounterNs(const struct SscTime *clock, uint64_t ticks, int64_t *ns)
{
    uint64_t seconds = ticks / clock->frequency_hz;
    uint64_t remainder = ticks % clock->frequency_hz;
    uint64_t value, fraction;
    if (__builtin_mul_overflow(seconds, NS_PER_SECOND, &value) ||
        __builtin_mul_overflow(remainder, NS_PER_SECOND, &fraction)) return -ERANGE;
    if (__builtin_add_overflow(value, fraction / clock->frequency_hz, &value))
        return -ERANGE;
    if (value > INT64_MAX) return -ERANGE;
    *ns = (int64_t)value;
    return 0;
}

static int RefreshLocked(struct SscTime *clock, int64_t update_time)
{
    int64_t before_ns, after_ns, boot_ns;
    for (unsigned int attempt = 0; attempt < SAMPLE_ATTEMPTS; ++attempt) {
        int result = CounterNs(clock, ReadCounter(), &before_ns);
        if (result) return result;
        result = ReadBootTime(&boot_ns);
        if (result) return result;
        result = CounterNs(clock, ReadCounter(), &after_ns);
        if (result) return result;
        if (after_ns < before_ns) return -ERANGE;
        /* 跨度过大时重采，最后一次沿用原厂的有界重试规则 */
        if ((uint64_t)(after_ns - before_ns) <= SAMPLE_SPAN_NS ||
            attempt + 1 == SAMPLE_ATTEMPTS) {
            clock->offset_ns = boot_ns - before_ns;
            clock->last_update_ns = update_time;
            return 0;
        }
    }
    return -EIO;
}

int SscTimeInit(struct SscTime *clock)
{
    if (clock == NULL) return -EINVAL;
    clock->frequency_hz = ReadFrequency();
    if (!clock->frequency_hz) return -ERANGE;
    int result = pthread_mutex_init(&clock->lock, NULL);
    if (result) return -result;
    int64_t now;
    result = ReadBootTime(&now);
    if (!result) result = RefreshLocked(clock, now);
    if (result) pthread_mutex_destroy(&clock->lock);
    return result;
}

int SscTimeDestroy(struct SscTime *clock)
{
    if (clock == NULL) return -EINVAL;
    return -pthread_mutex_destroy(&clock->lock);
}

int SscTimeRefresh(struct SscTime *clock)
{
    if (clock == NULL) return -EINVAL;
    int result = pthread_mutex_lock(&clock->lock);
    if (result) return -result;
    int64_t now;
    result = ReadBootTime(&now);
    if (!result) result = RefreshLocked(clock, now);
    pthread_mutex_unlock(&clock->lock);
    return result;
}

int SscTimeConvert(struct SscTime *clock, uint64_t ticks, int64_t *timestamp_ns)
{
    if (clock == NULL || timestamp_ns == NULL) return -EINVAL;
    int result = pthread_mutex_lock(&clock->lock);
    if (result) return -result;
    int64_t counter_ns, converted;
    result = CounterNs(clock, ticks, &counter_ns);
    if (!result && __builtin_add_overflow(counter_ns, clock->offset_ns, &converted))
        result = -ERANGE;
    if (!result && converted >= 1 &&
        (converted < clock->last_update_ns ||
        converted - clock->last_update_ns >= EVENT_REFRESH_NS)) {
        result = RefreshLocked(clock, converted);
        if (!result && __builtin_add_overflow(counter_ns, clock->offset_ns, &converted))
            result = -ERANGE;
    }
    if (!result) *timestamp_ns = converted;
    pthread_mutex_unlock(&clock->lock);
    return result;
}
