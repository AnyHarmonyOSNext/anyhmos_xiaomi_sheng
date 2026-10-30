/* USB ACM session recovery. Never rebind the controller or replay a command. */
static char serial_command_buffer[4096];
static size_t serial_command_length;
static int serial_command_overflow;
static unsigned serial_reopens,serial_failures;
static unsigned long long serial_rx_bytes,serial_tx_bytes;
static long long serial_retry_ms;
static long long serial_now_ms(void) {
    struct timespec ts;clock_gettime(CLOCK_MONOTONIC,&ts);
    return (long long)ts.tv_sec*1000+ts.tv_nsec/1000000;
}
static void serial_reset(const char *operation,int error) {
    if(serialfd>=0)close(serialfd);
    serialfd=-1;serial_command_length=0;serial_command_overflow=0;
    serial_pos=used;serial_retry_ms=serial_now_ms()+250;
    serial_failures++;
    /* Rate limit disconnected/no-host notifications, but retain counters. */
    if(serial_failures<=3||(serial_failures&(serial_failures-1))==0)
        note("USB session reset op=%s errno=%d count=%u rx=%llu tx=%llu; reopen only, no command retry",
             operation,error,serial_failures,serial_rx_bytes,serial_tx_bytes);
}
static void serial_tick(void) {
    if(serialfd<0&&usb_configured) {
        if(serial_now_ms()<serial_retry_ms)return;
        serial_retry_ms=serial_now_ms()+250;
        node_from_sys("/sys/class/tty/ttyGS0","/dev/ttyGS0",S_IFCHR);
        serialfd=open("/dev/ttyGS0",O_RDWR|O_NONBLOCK|O_NOCTTY|O_CLOEXEC);
        if(serialfd<0)return;
        struct termios t;
        if(tcgetattr(serialfd,&t)<0){serial_reset("tcgetattr",errno);return;}
        cfmakeraw(&t);t.c_cflag|=CLOCAL|CREAD;t.c_cflag&=~(HUPCL|CRTSCTS);
        if(tcsetattr(serialfd,TCSANOW,&t)<0){serial_reset("tcsetattr",errno);return;}
        serial_command_length=0;serial_command_overflow=0;
        /* Old boot logs stay on disk and remain available through replay. */
        serial_pos=used;serial_reopens++;
        note("USB ttyGS0 session ready v121 opens=%u failures=%u; raw -hupcl; commands unchanged",
             serial_reopens,serial_failures);
    }
    if(serialfd<0)return;
    struct pollfd state={.fd=serialfd,.events=POLLIN|POLLOUT};
    int ready=poll(&state,1,0);
    if(ready<0){if(errno!=EINTR)serial_reset("poll",errno);return;}
    if(state.revents&POLLNVAL){serial_reset("poll-nval",EBADF);return;}
    if((state.revents&(POLLHUP|POLLERR))&&!(state.revents&POLLIN)) {
        serial_reset("poll-hangup",EIO);return;
    }
    char bytes[512];ssize_t n=read(serialfd,bytes,sizeof(bytes));
    if(n<0&&errno!=EAGAIN&&errno!=EWOULDBLOCK&&errno!=EINTR) {
        serial_reset("read",errno);return;
    }
    if(n==0&&(state.revents&POLLHUP)){serial_reset("read-eof",0);return;}
    if(n>0)serial_rx_bytes+=(unsigned long long)n;
    for(ssize_t i=0;i<n;i++) {
        char c=bytes[i];
        if(c=='\r'||c=='\n') {
            if(serial_command_overflow)note("Serial command discarded: too long");
            else if(serial_command_length) {
                serial_command_buffer[serial_command_length]=0;
                serial_command(serial_command_buffer);
            }
            serial_command_length=0;serial_command_overflow=0;
        } else if(serial_command_length+1<sizeof(serial_command_buffer)) {
            serial_command_buffer[serial_command_length++]=c;
        } else serial_command_overflow=1;
    }
    if(serial_pos<used&&(state.revents&POLLOUT)) {
        size_t z=used-serial_pos;if(z>4096)z=4096;
        n=write(serialfd,history+serial_pos,z);
        if(n>0){serial_pos+=(size_t)n;serial_tx_bytes+=(unsigned long long)n;}
        else if(n<0&&errno!=EAGAIN&&errno!=EWOULDBLOCK&&errno!=EINTR)
            serial_reset("write",errno);
    }
}
