/* SPDX-License-Identifier: MIT */
#ifndef SHENG_PAL_CLIENT_H
#define SHENG_PAL_CLIENT_H
#include "protocol.h"
int sheng_pal_connect(void);
int sheng_pal_request(int fd, uint32_t op, uint32_t arg0, uint32_t arg1,
    const void *pcm, uint32_t bytes, struct sheng_pal_reply *reply);
#endif
