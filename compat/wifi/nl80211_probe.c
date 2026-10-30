/* Bounded nl80211 radio scan. Reports aggregate results without SSIDs/MACs. */
#define _GNU_SOURCE
#include <errno.h>
#include <linux/genetlink.h>
#include <linux/netlink.h>
#include <linux/nl80211.h>
#include <net/if.h>
#include <poll.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/ioctl.h>
#include <sys/socket.h>
#include <time.h>
#include <unistd.h>

struct message { struct nlmsghdr n; struct genlmsghdr g; char a[4096]; };
static uint32_t seq;
static int fd;
static long long now_ms(void) {
    struct timespec t; clock_gettime(CLOCK_MONOTONIC, &t);
    return (long long)t.tv_sec * 1000 + t.tv_nsec / 1000000;
}
static struct nlattr *attr(void *p, int size, unsigned type) {
    for (struct nlattr *a = p; size >= (int)sizeof(*a); ) {
        if (a->nla_len < sizeof(*a) || a->nla_len > size) return NULL;
        if ((a->nla_type & NLA_TYPE_MASK) == type) return a;
        int step = NLA_ALIGN(a->nla_len); size -= step;
        a = (struct nlattr *)((char *)a + step);
    }
    return NULL;
}
static void *data(struct nlattr *a) { return (char *)a + NLA_HDRLEN; }
static int len(struct nlattr *a) { return a->nla_len - NLA_HDRLEN; }
static uint32_t u32(struct nlattr *a) { uint32_t v = 0; if (a && len(a) >= 4) memcpy(&v, data(a), 4); return v; }
static void init_msg(struct message *m, int type, int cmd, int flags) {
    memset(m, 0, sizeof(*m));
    m->n.nlmsg_len = NLMSG_LENGTH(GENL_HDRLEN);
    m->n.nlmsg_type = type; m->n.nlmsg_flags = NLM_F_REQUEST | flags;
    m->n.nlmsg_seq = ++seq; m->g.cmd = cmd; m->g.version = 1;
}
static void add(struct message *m, int type, const void *p, size_t n) {
    size_t at = NLMSG_ALIGN(m->n.nlmsg_len), space = NLA_ALIGN(NLA_HDRLEN + n);
    if (at + space > sizeof(*m)) { fprintf(stderr, "oversized request\n"); exit(2); }
    struct nlattr *a = (void *)((char *)m + at);
    a->nla_type = type; a->nla_len = NLA_HDRLEN + n;
    if (n) memcpy(data(a), p, n);
    m->n.nlmsg_len = at + space;
}
static int send_msg(struct message *m) {
    struct sockaddr_nl kernel = {.nl_family = AF_NETLINK};
    return sendto(fd, m, m->n.nlmsg_len, 0, (void *)&kernel, sizeof(kernel)) < 0 ? -errno : 0;
}
static int receive(char *buf, size_t size, long long deadline) {
    long long left = deadline - now_ms(); if (left <= 0) return -ETIMEDOUT;
    struct pollfd p = {.fd = fd, .events = POLLIN};
    int r = poll(&p, 1, (int)left); if (r <= 0) return r ? -errno : -ETIMEDOUT;
    struct sockaddr_nl from = {0}; socklen_t flen = sizeof(from);
    r = recvfrom(fd, buf, size, 0, (void *)&from, &flen);
    if (r < 0) return -errno;
    if (from.nl_pid != 0) return -EPROTO;
    return r;
}
static int error_of(struct nlmsghdr *h) {
    if (h->nlmsg_len < NLMSG_LENGTH(sizeof(struct nlmsgerr))) return -EPROTO;
    return ((struct nlmsgerr *)NLMSG_DATA(h))->error;
}
static int family(uint32_t *group) {
    struct message m; char buf[65536];
    init_msg(&m, GENL_ID_CTRL, CTRL_CMD_GETFAMILY, 0);
    add(&m, CTRL_ATTR_FAMILY_NAME, "nl80211", sizeof("nl80211"));
    int r = send_msg(&m); if (r) return r;
    long long deadline = now_ms() + 3000;
    for (;;) {
        r = receive(buf, sizeof(buf), deadline); if (r < 0) return r;
        for (struct nlmsghdr *h = (void *)buf; NLMSG_OK(h, r); h = NLMSG_NEXT(h, r)) {
            if (h->nlmsg_seq != seq) continue;
            if (h->nlmsg_type == NLMSG_ERROR) return error_of(h);
            if (h->nlmsg_len < NLMSG_LENGTH(GENL_HDRLEN)) return -EPROTO;
            void *p = (char *)NLMSG_DATA(h) + GENL_HDRLEN;
            int size = h->nlmsg_len - NLMSG_LENGTH(GENL_HDRLEN);
            struct nlattr *id = attr(p, size, CTRL_ATTR_FAMILY_ID);
            if (!id || len(id) != 2) return -EPROTO;
            uint16_t number; memcpy(&number, data(id), 2);
            struct nlattr *groups = attr(p, size, CTRL_ATTR_MCAST_GROUPS);
            if (groups) {
                int remain = len(groups);
                for (struct nlattr *a = data(groups); remain >= NLA_HDRLEN; ) {
                    if (a->nla_len < NLA_HDRLEN || a->nla_len > remain) return -EPROTO;
                    struct nlattr *name = attr(data(a), len(a), CTRL_ATTR_MCAST_GRP_NAME);
                    struct nlattr *gid = attr(data(a), len(a), CTRL_ATTR_MCAST_GRP_ID);
                    if (name && len(name) == 5 && !memcmp(data(name), "scan", 5)) *group = u32(gid);
                    int step = NLA_ALIGN(a->nla_len); remain -= step; a = (void *)((char *)a + step);
                }
            }
            return number;
        }
    }
}
static int bring_up(const char *name) {
    int s = socket(AF_INET, SOCK_DGRAM | SOCK_CLOEXEC, 0); if (s < 0) return -errno;
    struct ifreq req = {0}; snprintf(req.ifr_name, sizeof(req.ifr_name), "%s", name);
    int r = ioctl(s, SIOCGIFFLAGS, &req);
    if (!r) { req.ifr_flags |= IFF_UP; r = ioctl(s, SIOCSIFFLAGS, &req); }
    int result = r ? -errno : 0; close(s); return result;
}
int main(int argc, char **argv) {
    if (argc != 2 || strlen(argv[1]) >= IFNAMSIZ) return 2;
    setvbuf(stdout, NULL, _IOLBF, 0);
    unsigned iface = if_nametoindex(argv[1]); if (!iface) { perror("if_nametoindex"); return 3; }
    fd = socket(AF_NETLINK, SOCK_RAW | SOCK_CLOEXEC, NETLINK_GENERIC); if (fd < 0) { perror("netlink"); return 3; }
    struct sockaddr_nl local = {.nl_family = AF_NETLINK};
    if (bind(fd, (void *)&local, sizeof(local))) { perror("bind"); return 3; }
    uint32_t group = 0; int id = family(&group);
    printf("NL80211_FAMILY=%d SCAN_GROUP=%u IFINDEX=%u\n", id, group, iface);
    if (id <= 0 || !group) return 4;
    if (setsockopt(fd, SOL_NETLINK, NETLINK_ADD_MEMBERSHIP, &group, sizeof(group))) { perror("membership"); return 4; }
    int r = bring_up(argv[1]); printf("INTERFACE_UP=%d\n", r); if (r) return 5;
    struct message m; char buf[65536];
    init_msg(&m, id, NL80211_CMD_TRIGGER_SCAN, NLM_F_ACK);
    add(&m, NL80211_ATTR_IFINDEX, &iface, sizeof(iface));
    // No scan SSIDs means passive scan; no saved-network names are transmitted.
    if (send_msg(&m)) return 6;
    long long deadline = now_ms() + 35000; int done = 0;
    while (!done) {
        r = receive(buf, sizeof(buf), deadline); if (r < 0) { printf("SCAN_WAIT=%d\n", r); return 7; }
        for (struct nlmsghdr *h = (void *)buf; NLMSG_OK(h, r); h = NLMSG_NEXT(h, r)) {
            if (h->nlmsg_type == NLMSG_ERROR && h->nlmsg_seq == seq) {
                int e = error_of(h); printf("SCAN_TRIGGER_ACK=%d\n", e); if (e) return 6;
            } else if (h->nlmsg_type == id && h->nlmsg_len >= NLMSG_LENGTH(GENL_HDRLEN)) {
                struct genlmsghdr *g = NLMSG_DATA(h);
                if (g->cmd == NL80211_CMD_SCAN_ABORTED) { puts("SCAN_ABORTED=1"); return 7; }
                if (g->cmd == NL80211_CMD_NEW_SCAN_RESULTS) { done = 1; break; }
            }
        }
    }
    puts("SCAN_COMPLETED=1");
    init_msg(&m, id, NL80211_CMD_GET_SCAN, NLM_F_DUMP);
    add(&m, NL80211_ATTR_IFINDEX, &iface, sizeof(iface));
    if (send_msg(&m)) return 8;
    deadline = now_ms() + 5000; int count = 0, low = 0, high = 0, six = 0;
    for (;;) {
        r = receive(buf, sizeof(buf), deadline); if (r < 0) return 8;
        for (struct nlmsghdr *h = (void *)buf; NLMSG_OK(h, r); h = NLMSG_NEXT(h, r)) {
            if (h->nlmsg_seq != seq) continue;
            if (h->nlmsg_type == NLMSG_DONE) {
                printf("BSS_COUNT=%d BAND_2G=%d BAND_5G=%d BAND_6G=%d\n", count, low, high, six);
                close(fd); return count ? 0 : 9;
            }
            if (h->nlmsg_type == NLMSG_ERROR) { printf("SCAN_DUMP_ERROR=%d\n", error_of(h)); return 8; }
            if (h->nlmsg_len < NLMSG_LENGTH(GENL_HDRLEN)) return 8;
            void *p = (char *)NLMSG_DATA(h) + GENL_HDRLEN;
            struct nlattr *bss = attr(p, h->nlmsg_len - NLMSG_LENGTH(GENL_HDRLEN), NL80211_ATTR_BSS);
            if (!bss) continue;
            uint32_t freq = u32(attr(data(bss), len(bss), NL80211_BSS_FREQUENCY));
            ++count; if (freq < 3000) ++low; else if (freq < 5925) ++high; else ++six;
        }
    }
}
