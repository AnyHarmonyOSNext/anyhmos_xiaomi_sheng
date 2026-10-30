/* SPDX-License-Identifier: MIT
 * Original ALSA control inspection. No write, configuration, or PCM start.
 */
#include <sys/ioctl.h>
#include <sound/asound.h>
#include <fcntl.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>
#include <errno.h>

int main(int argc, char **argv)
{
    if (argc != 2) return 2;
    int fd = open(argv[1], O_RDONLY | O_CLOEXEC | O_NOFOLLOW);
    if (fd < 0) { perror("control open"); return 3; }
    struct snd_ctl_card_info card = {0};
    if (ioctl(fd, SNDRV_CTL_IOCTL_CARD_INFO, &card)) { perror("CARD_INFO"); return 4; }
    printf("CARD=%d ID=%.16s DRIVER=%.16s NAME=%.32s\n", card.card, card.id, card.driver, card.name);
    struct snd_ctl_elem_list list = {0};
    if (ioctl(fd, SNDRV_CTL_IOCTL_ELEM_LIST, &list) || list.count > 8192) return 5;
    list.space = list.count;
    list.pids = calloc(list.count, sizeof(*list.pids));
    if (!list.pids || ioctl(fd, SNDRV_CTL_IOCTL_ELEM_LIST, &list)) return 6;
    printf("CONTROL_COUNT=%u\n", list.count);
    unsigned failures = 0;
    for (unsigned i = 0; i < list.used; i++) {
        struct snd_ctl_elem_info info = {.id = list.pids[i]};
        if (ioctl(fd, SNDRV_CTL_IOCTL_ELEM_INFO, &info)) { failures++; continue; }
        printf("CTL id=%u name=\"%.44s\" type=%u count=%u access=0x%x", info.id.numid, info.id.name, info.type, info.count, info.access);
        if (info.type == SNDRV_CTL_ELEM_TYPE_INTEGER || info.type == SNDRV_CTL_ELEM_TYPE_BOOLEAN)
            printf(" range=%ld:%ld:%ld", info.value.integer.min, info.value.integer.max, info.value.integer.step);
        if (info.type == SNDRV_CTL_ELEM_TYPE_ENUMERATED) {
            unsigned items = info.value.enumerated.items;
            printf(" items=%u", items);
            for (unsigned j = 0; j < items && j < 64; j++) {
                info.value.enumerated.item = j;
                if (!ioctl(fd, SNDRV_CTL_IOCTL_ELEM_INFO, &info))
                    printf(" [%u]=\"%.64s\"", j, info.value.enumerated.name);
            }
        }
        if ((info.access & SNDRV_CTL_ELEM_ACCESS_READ) && info.type != SNDRV_CTL_ELEM_TYPE_BYTES) {
            struct snd_ctl_elem_value value = {.id = info.id};
            if (!ioctl(fd, SNDRV_CTL_IOCTL_ELEM_READ, &value)) {
                printf(" current=");
                for (unsigned j = 0; j < info.count && j < 8; j++) {
                    if (j) putchar(',');
                    if (info.type == SNDRV_CTL_ELEM_TYPE_ENUMERATED) printf("%u", value.value.enumerated.item[j]);
                    else if (info.type == SNDRV_CTL_ELEM_TYPE_INTEGER || info.type == SNDRV_CTL_ELEM_TYPE_BOOLEAN) printf("%ld", value.value.integer.value[j]);
                    else printf("?");
                }
            } else printf(" read_errno=%d", errno);
        }
        putchar('\n');
    }
    printf("READONLY_CONTROL_INFO_FAILURES=%u\n", failures);
    free(list.pids);
    close(fd);
    return failures ? 7 : 0;
}
