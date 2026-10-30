/* SPDX-License-Identifier: MIT */
#ifndef SHENG_PAL_PROTOCOL_H
#define SHENG_PAL_PROTOCOL_H
#include <stdint.h>
#define SHENG_PAL_MAGIC 0x53415031u
#define SHENG_PAL_SOCKET "sheng.pal.pcm.v1"
#define SHENG_PAL_MAX_DATA 61440u
enum sheng_pal_op {
    SHENG_PAL_OPEN=1, SHENG_PAL_START, SHENG_PAL_WRITE, SHENG_PAL_VOLUME,
    SHENG_PAL_STOP, SHENG_PAL_CLOSE, SHENG_PAL_PAUSE, SHENG_PAL_RESUME,
    SHENG_PAL_STATUS
};
struct sheng_pal_request {
    uint32_t magic, op, bytes, sequence, arg0, arg1;
};
struct sheng_pal_reply {
    uint32_t magic, sequence;
    int32_t rc;
    uint32_t bytes;
    uint64_t written_frames;
};
_Static_assert(sizeof(struct sheng_pal_request)==24, "fixed wire header");
_Static_assert(sizeof(struct sheng_pal_reply)==24, "fixed wire reply");
#endif
