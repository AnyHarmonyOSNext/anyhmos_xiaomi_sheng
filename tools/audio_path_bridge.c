/* Redirect an explicit set of original audio XML reads into /compat.
 * No vendor mount overlays; writes to redirected source configs are refused.
 */
typedef unsigned long size_t;
typedef long ssize_t;
extern int strcmp(const char *, const char *);
extern int snprintf(char *, size_t, const char *, ...);
extern void *dlsym(void *, const char *);
extern ssize_t write(int, const void *, size_t);
extern int *__errno(void);

static const char *map(const char *p, char *out, size_t size)
{
    if (!p) return p;
    static const struct { const char *from, *to; } fixed[] = {
        {"/vendor/etc/card-defs.xml", "vendor/etc/card-defs.xml"},
        {"/vendor/etc/kvh2xml.xml", "vendor/etc/kvh2xml.xml"},
        {"/vendor/etc/usecaseKvManager.xml", "vendor/etc/usecaseKvManager.xml"},
        {"/odm/etc/usecaseKvManager.xml", "odm/etc/usecaseKvManager.xml"},
    };
    const char *dest = 0;
    for (size_t i=0; i<sizeof(fixed)/sizeof(fixed[0]); i++)
        if (!strcmp(p, fixed[i].from)) dest = fixed[i].to;
    if (dest) {
        (void)snprintf(out, size, "/compat/audio-supplement-v1/config/%s", dest);
    } else {
        const char *names[] = {"mixer_paths_kalama_mtp.xml", "mixer_paths_overlay_static.xml",
            "mixer_paths_overlay_dynamic.xml", "resourcemanager_kalama_mtp.xml"};
        const char *prefixes[] = {"/vendor/etc/", "/vendor/etc/audio/sku_kalama/", "/odm/etc/audio/sku_kalama/"};
        for (size_t i=0; i<sizeof(names)/sizeof(names[0]); i++) {
            for (size_t j=0; j<sizeof(prefixes)/sizeof(prefixes[0]); j++) {
                char candidate[160];
                (void)snprintf(candidate, sizeof(candidate), "%s%s", prefixes[j], names[i]);
                if (!strcmp(p, candidate)) {
                    (void)snprintf(out, size, "/compat/audio-supplement-v1/config/odm/etc/audio/sku_kalama/%s", names[i]);
                    dest = names[i];
                }
            }
        }
        if (!dest) return p;
    }
    static unsigned count;
    if (count++ < 80) {
        char b[440];
        int n = snprintf(b, sizeof(b), "AUDIO_PATH=%s -> %s\n", p, out);
        if (n > 0 && n < (int)sizeof(b)) (void)write(1, b, (size_t)n);
    }
    return out;
}

void *fopen(const char *path, const char *mode)
{
    char mapped[256];
    const char *p = map(path, mapped, sizeof(mapped));
    if (p != path && (!mode || strcmp(mode, "r") && strcmp(mode, "rb"))) {
        *__errno() = 30;
        return 0;
    }
    void *(*next)(const char *, const char *) = dlsym((void *)-1L, "fopen");
    if (!next) { *__errno() = 38; return 0; }
    return next(p, mode);
}

int access(const char *path, int mode)
{
    char mapped[256];
    const char *p = map(path, mapped, sizeof(mapped));
    if (p != path && (mode & 2)) { *__errno() = 30; return -1; }
    int (*next)(const char *, int) = dlsym((void *)-1L, "access");
    if (!next) { *__errno() = 38; return -1; }
    return next(p, mode);
}
