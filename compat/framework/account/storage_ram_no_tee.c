/* SPDX-License-Identifier: MIT
 * RAM-data boot trial only: report the unavailable HUKS HDI immediately.
 * The original daemon already skips encryption when fscrypt is not enabled;
 * this also lets its optional authentication-format upgrade query return
 * "unsupported", instead of connecting to a nonexistent Huawei TEE forever.
 */
#define _GNU_SOURCE
#include <stdbool.h>
#include <stddef.h>
#include <string.h>
#include <dlfcn.h>
struct IHuks;
struct IHuks *IHuksGetInstance(const char *name,bool direct)
{
    if(name&&direct&&!strcmp(name,"hdi_service"))return NULL;
    typedef struct IHuks *(*Get)(const char*,bool);
    Get get=(Get)dlsym(RTLD_NEXT,"IHuksGetInstance");return get?get(name,direct):NULL;
}
