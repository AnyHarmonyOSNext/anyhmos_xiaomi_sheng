#pragma once
#include <cstdarg>
#include <cstdio>
#include <dlfcn.h>
#include "hilog/log_c.h"
inline void Ace5Log(const char *format, ...)
{
    char message[512]; va_list args;
    va_start(args, format); vsnprintf(message, sizeof(message), format, args); va_end(args);
    fprintf(stderr, "ACE5_DISPLAY %s\n", message);
    // The unmodified native host already loads libhilog. Early contract tests
    // intentionally work before hilogd and without adding another dependency.
    static auto print = reinterpret_cast<decltype(&HiLogPrint)>(dlsym(RTLD_DEFAULT, "HiLogPrint"));
    // This ROM filters INFO globally during early boot. Keep bring-up evidence
    // visible without changing its global logging configuration.
    if (print) print(LOG_CORE, LOG_WARN, 0xD002515, "ACE5_DISPLAY", "%{public}s", message);
}
