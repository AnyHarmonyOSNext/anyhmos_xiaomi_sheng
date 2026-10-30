/* SPDX-License-Identifier: MIT
 * Keep the original virtual mixer alive until PAL has joined its event thread.
 * Real mixer operations and AGM events are preserved. No status is fabricated.
 */
typedef unsigned long size_t;
typedef long ssize_t;
extern void *dlsym(void *, const char *);
extern void *dlopen(const char *, int);
extern int snprintf(char *, size_t, const char *, ...);
extern ssize_t write(int, const void *, size_t);
static void *virtual_mixer;
static void *deferred_mixer;
static int deinit_active;
static int mixer_closing;

static void log_state(const char *event, void *p)
{
    char b[128];
    int n=snprintf(b, sizeof(b), "PAL_LIFECYCLE_%s=%p\n", event, p);
    if (n>0 && n<(int)sizeof(b)) (void)write(1, b, (size_t)n);
}

void *mixer_open(unsigned card)
{
    void *(*real)(unsigned)=dlsym((void *)-1L, "mixer_open");
    if (!real) return 0;
    void *p=real(card);
    if (p && card==100) {
            __atomic_store_n(&mixer_closing, 0, __ATOMIC_RELEASE);
            __atomic_store_n(&virtual_mixer, p, __ATOMIC_RELEASE);
            log_state("VIRTUAL_OPEN", p);
    }
    return p;
}

int mixer_wait_event(void *p, int timeout_ms)
{
    if (p==__atomic_load_n(&virtual_mixer, __ATOMIC_ACQUIRE)) {
        if (__atomic_load_n(&mixer_closing, __ATOMIC_ACQUIRE)) return -19;
        /* The original implementation polls a real plugin fd with this bound. */
        if (timeout_ms<0 || timeout_ms>100) timeout_ms=100;
    }
    int (*real)(void *, int)=dlsym((void *)-1L, "mixer_wait_event");
    return real ? real(p, timeout_ms) : -38;
}

void mixer_close(void *p)
{
    if (p && p==__atomic_load_n(&virtual_mixer, __ATOMIC_ACQUIRE) &&
        __atomic_load_n(&deinit_active, __ATOMIC_ACQUIRE)) {
        __atomic_store_n(&mixer_closing, 1, __ATOMIC_RELEASE);
        __atomic_store_n(&deferred_mixer, p, __ATOMIC_RELEASE);
        log_state("DEFER_CLOSE", p);
        return;
    }
    void (*real)(void *)=dlsym((void *)-1L, "mixer_close");
    if (real) real(p);
}

void pal_deinit(void)
{
    log_state("DEINIT_ENTER", __atomic_load_n(&virtual_mixer, __ATOMIC_ACQUIRE));
    /* The existing original DSO owns the PAL state. Never unload it here. */
    void *h=dlopen("libar-pal.so", 2|4); /* RTLD_NOW | RTLD_NOLOAD */
    void (*real)(void)=h ? dlsym(h, "pal_deinit") : 0;
    if (!real || real==pal_deinit) {
        log_state("DEINIT_SYMBOL_ERROR", h);
        return;
    }
    __atomic_store_n(&deinit_active, 1, __ATOMIC_RELEASE);
    real();
    /* Original ResourceManager::deinit has now joined the mixer event thread. */
    void *p=__atomic_exchange_n(&deferred_mixer, (void *)0, __ATOMIC_ACQ_REL);
    if (p) {
        __atomic_store_n(&virtual_mixer, (void *)0, __ATOMIC_RELEASE);
        void (*close_fn)(void *)=dlsym((void *)-1L, "mixer_close");
        if (close_fn) close_fn(p);
        log_state("RELEASE_AFTER_JOIN", p);
    }
    __atomic_store_n(&deinit_active, 0, __ATOMIC_RELEASE);
    log_state("DEINIT_RETURNED", p);
}
