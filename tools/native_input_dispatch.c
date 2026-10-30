// Run the donor's original input tool under an init service's native identity.
// Only bounded, explicit input arguments from our debug file are accepted.
#include <ctype.h>
#include <stdio.h>
#include <string.h>
#include <unistd.h>
int main(void)
{
    alarm(10);
    FILE *f = fopen("/data/local/tmp/sheng-input.args", "r");
    if (!f) return 2;
    char values[20][32];
    char *args[22] = {"/compat/bin/uinput-original"};
    unsigned count = 0;
    while (count < 20 && fscanf(f, "%31s", values[count]) == 1) {
        for (const unsigned char *p = (unsigned char *)values[count]; *p; ++p)
            if (!isalnum(*p) && *p != '-' && *p != '.') { fclose(f); return 3; }
        args[count + 1] = values[count];
        ++count;
    }
    int extra = fgetc(f);
    fclose(f);
    if (count < 2 || (extra != EOF && !isspace((unsigned char)extra))) return 4;
    args[count + 1] = NULL;
    if (!freopen("/data/local/tmp/sheng-input-last.log", "w", stdout)) return 5;
    dup2(fileno(stdout), STDERR_FILENO);
    setbuf(stdout, NULL);
    printf("NATIVE_INPUT uid=%d argc=%u\n", getuid(), count);
    execv(args[0], args);
    perror("execv");
    return 6;
}
