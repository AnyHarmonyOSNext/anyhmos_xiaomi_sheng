#ifndef SSC_TIME_H
#define SSC_TIME_H

#include <pthread.h>
#include <stdint.h>

#ifdef __cplusplus
extern "C" {
#endif

#define SSC_TIME_REFRESH_PERIOD_NS UINT64_C(30000000000)

struct SscTime {
    pthread_mutex_t lock;
    uint64_t frequency_hz;
    int64_t offset_ns;
    int64_t last_update_ns;
};

/* 初始化后可并发换算；销毁前须结束全部使用者 */
int SscTimeInit(struct SscTime *clock);
int SscTimeDestroy(struct SscTime *clock);
/* 每30秒及唤醒后调用，更新计数器与启动时钟的偏移 */
int SscTimeRefresh(struct SscTime *clock);
/* 输出包含休眠时间的启动纳秒；失败时不改写输出 */
int SscTimeConvert(struct SscTime *clock, uint64_t ticks, int64_t *timestamp_ns);

#ifdef __cplusplus
}
#endif
#endif
