/* Isolated acceptance helper for the exact assembly deployed in donor MemMgr. */
#include <stdio.h>
#include <stdlib.h>
extern int sheng_memavailable_kb(void);
int main(int argc, char **argv) {
    int value = sheng_memavailable_kb();
    printf("REAL_MEMAVAILABLE_KB=%d\n", value);
    if (argc == 2) return value == strtol(argv[1], NULL, 10) ? 0 : 3;
    return value > 0 && value < 2147483647 ? 0 : 4;
}
