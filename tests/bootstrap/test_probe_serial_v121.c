/* Exercise the production transport against Linux PTYs, including hangup. */
#define _GNU_SOURCE
#include <assert.h>
#include <errno.h>
#include <fcntl.h>
#include <poll.h>
#include <stdarg.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/stat.h>
#include <termios.h>
#include <time.h>
#include <unistd.h>
static int serialfd=-1,usb_configured=1,commands;
static char history[65536],slave_path[128],last_command[4096];
static size_t used,serial_pos;
static void note(const char *fmt,...) {(void)fmt;}
static void node_from_sys(const char *a,const char *b,int mode) {(void)a;(void)b;(void)mode;}
static void serial_command(char *s) {commands++;snprintf(last_command,sizeof(last_command),"%s",s);}
static int tty_open(const char *path,int flags) {
    assert(!strcmp(path,"/dev/ttyGS0"));return open(slave_path,flags);
}
#define open tty_open
#include "../../compat/bootstrap/probe_serial_v121.inc"
#undef open
static int make_host(void) {
    int fd=posix_openpt(O_RDWR|O_NOCTTY|O_NONBLOCK);assert(fd>=0);
    assert(grantpt(fd)==0&&unlockpt(fd)==0);
    snprintf(slave_path,sizeof(slave_path),"%s",ptsname(fd));return fd;
}
static void receive_text(int host,const char *s) {
    size_t n=strlen(s);assert(write(host,s,n)==(ssize_t)n);
    for(int i=0;i<30;i++){serial_tick();usleep(1000);}
}
int main(void) {
    int host=make_host();serial_tick();assert(serialfd>=0);
    struct termios t;assert(tcgetattr(serialfd,&t)==0);
    assert(!(t.c_cflag&HUPCL)&&!(t.c_lflag&(ICANON|ECHO)));
    receive_text(host,"status\n");assert(commands==1&&!strcmp(last_command,"status"));
    receive_text(host,"partial-old-request");assert(commands==1);
    close(host);serial_tick();assert(serialfd<0&&serial_failures==1);
    host=make_host();serial_retry_ms=0;serial_tick();assert(serialfd>=0&&serial_reopens==2);
    receive_text(host,"status\n");assert(commands==2&&!strcmp(last_command,"status"));
    /* No repeat of a previously executed command on a new session. */
    for(int i=0;i<10;i++)serial_tick();
    assert(commands==2);
    /* A non-reading host must not turn TX EAGAIN into a reconnect loop. */
    memset(history,'x',sizeof(history));used=sizeof(history);serial_pos=0;
    for(int i=0;i<1000;i++)serial_tick();
    assert(serial_failures==1);
    char drain[65536];while(read(host,drain,sizeof(drain))>0){}
    serial_pos=used;
    char long_line[4200];memset(long_line,'a',sizeof(long_line)-1);long_line[sizeof(long_line)-1]=0;
    receive_text(host,long_line);receive_text(host,"\nstatus\n");
    assert(commands==3&&!strcmp(last_command,"status"));
    close(host);close(serialfd);
    puts("PASS raw-no-HUPCL, fragmented-input, hangup-reopen, discard-stale-input, no-command-retry, TX-backpressure, overflow-recovery");
    return 0;
}
