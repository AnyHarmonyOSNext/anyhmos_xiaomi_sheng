/* Bounded read-only AGM initialization probe for the original 303 Bionic libs.
 * Loaded into the original agmplay with LD_PRELOAD; it exits before agmplay.
 */
typedef unsigned long size_t;
typedef long ssize_t;
extern void *dlopen(const char *, int);
extern void *dlsym(void *, const char *);
extern char *dlerror(void);
extern int snprintf(char *, size_t, const char *, ...);
extern int vsnprintf(char *, size_t, const char *, __builtin_va_list);
extern ssize_t write(int, const void *, size_t);
extern void _exit(int);
extern void *calloc(size_t, size_t);
extern void free(void *);

struct aif_info { char name[32]; int direction; };

int __android_log_print(int priority, const char *tag, const char *fmt, ...)
{
    char b[768];
    int n = snprintf(b, sizeof(b), "AGM_LOG_%d_%s: ", priority,
                     tag ? tag : "?");
    if (n < 0 || n >= (int)sizeof(b)) return 0;
    __builtin_va_list ap;
    __builtin_va_start(ap, fmt);
    int m = vsnprintf(b + n, sizeof(b) - (size_t)n, fmt, ap);
    __builtin_va_end(ap);
    if (m < 0) return 0;
    size_t used = (size_t)n + (size_t)m;
    if (used >= sizeof(b) - 2) used = sizeof(b) - 2;
    b[used++] = '\n';
    (void)write(1, b, used);
    return m;
}

int ar_log(int level, const char *module, const char *file, int line,
           const char *fmt, ...)
{
    static int seen;
    if (seen++ >= 400) return 0;
    char b[768];
    int n = snprintf(b, sizeof(b), "AR_LOG_%d_%s:%d: ", level,
                     module ? module : "?", line);
    if (n < 0 || n >= (int)sizeof(b)) return 0;
    __builtin_va_list ap;
    __builtin_va_start(ap, fmt);
    int m = vsnprintf(b + n, sizeof(b) - (size_t)n, fmt, ap);
    __builtin_va_end(ap);
    if (m < 0) return 0;
    size_t used = (size_t)n + (size_t)m;
    if (used >= sizeof(b) - 2) used = sizeof(b) - 2;
    b[used++] = '\n';
    (void)write(1, b, used);
    return m;
}

static void say(const char *label, int value)
{
    char b[128];
    int n = snprintf(b, sizeof(b), "%s=%d\n", label, value);
    if (n > 0 && n < (int)sizeof(b)) (void)write(1, b, (size_t)n);
}

static void fail(const char *label)
{
    char b[256];
    char *err = dlerror();
    int n = snprintf(b, sizeof(b), "%s=%s\n", label, err ? err : "unknown");
    if (n > 0 && n < (int)sizeof(b)) (void)write(1, b, (size_t)n);
    _exit(80);
}

__attribute__((constructor)) static void run(void)
{
    void *h = dlopen("libagm.so", 2);
    if (!h) fail("AGM_DLOPEN_ERROR");
    int (*agm_init_fn)(void) = (int (*)(void))dlsym(h, "agm_init");
    if (!agm_init_fn) fail("AGM_INIT_SYMBOL_ERROR");
    int (*agm_deinit_fn)(void) = (int (*)(void))dlsym(h, "agm_deinit");
    if (!agm_deinit_fn) fail("AGM_DEINIT_SYMBOL_ERROR");
    int (*get_aif_fn)(void *, size_t *) =
        (int (*)(void *, size_t *))dlsym(h, "agm_get_aif_info_list");
    if (!get_aif_fn) fail("AGM_AIF_SYMBOL_ERROR");
    say("AGM_DLOPEN", 1);
    int rc = agm_init_fn();
    say("AGM_INIT_RC", rc);
    if (rc == 0) {
        size_t count = 0;
        int qrc = get_aif_fn(0, &count);
        say("AGM_AIF_QUERY_RC", qrc);
        say("AGM_AIF_COUNT", count > 2147483647UL ? -1 : (int)count);
        if (qrc == 0 && count > 0 && count <= 128) {
            struct aif_info *list = calloc(count, sizeof(*list));
            if (list) {
                size_t capacity = count;
                qrc = get_aif_fn(list, &count);
                say("AGM_AIF_LIST_RC", qrc);
                if (qrc == 0 && count <= capacity) {
                    for (size_t i = 0; i < count; i++) {
                        char b[128];
                        int n = snprintf(b, sizeof(b), "AGM_AIF_%lu=%.32s DIR=%d\n",
                                         i, list[i].name, list[i].direction);
                        if (n > 0 && n < (int)sizeof(b)) (void)write(1, b, (size_t)n);
                    }
                }
                free(list);
            }
        }
        int drc = agm_deinit_fn();
        say("AGM_DEINIT_RC", drc);
    }
    _exit(rc == 0 ? 0 : 81);
}
