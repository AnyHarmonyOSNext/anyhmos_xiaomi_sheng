// SPDX-License-Identifier: Apache-2.0
// Stock sheng THP mmap transport -> standard Linux uinput; vendor remains intact.
// Touch algorithm and filter adapted from upstream xiaomi-sheng-thp; see ORIGIN.md.
#include "nvt_touch_core.hpp"
#include "nvt_finger_filter.hpp"
#include <algorithm>
#include <array>
#include <cerrno>
#include <csignal>
#include <cstdio>
#include <cstdlib>
#include <cstring>
#include <fcntl.h>
#include <linux/input.h>
#include <linux/uinput.h>
#include <poll.h>
#include <sys/ioctl.h>
#include <sys/mman.h>
#include <sys/file.h>
#include <time.h>
#include <unistd.h>

static volatile sig_atomic_t running=1;
static void stop(int){running=0;}
static double now(){timespec t{};clock_gettime(CLOCK_MONOTONIC,&t);return t.tv_sec+t.tv_nsec/1e9;}
static uint16_t le16(const uint8_t*p){return uint16_t(p[0])|(uint16_t(p[1])<<8);}

class TouchOutput {
    int fd_=-1;
    std::array<int,nvt::kFingerSlots> active_{};
public:
    bool setup(){
        active_.fill(-1);fd_=open("/dev/uinput",O_WRONLY|O_NONBLOCK|O_CLOEXEC);
        if(fd_<0)return false;
        for(int type:{EV_KEY,EV_ABS})if(ioctl(fd_,UI_SET_EVBIT,type)<0)return false;
        for(int key:{BTN_TOUCH,BTN_TOOL_FINGER})if(ioctl(fd_,UI_SET_KEYBIT,key)<0)return false;
        for(int axis:{ABS_MT_SLOT,ABS_MT_TRACKING_ID,ABS_MT_POSITION_X,ABS_MT_POSITION_Y,ABS_MT_PRESSURE,ABS_MT_TOUCH_MAJOR})
            if(ioctl(fd_,UI_SET_ABSBIT,axis)<0)return false;
        if(ioctl(fd_,UI_SET_PROPBIT,INPUT_PROP_DIRECT)<0)return false;
        uinput_setup cfg{};cfg.id.bustype=BUS_VIRTUAL;cfg.id.vendor=0x2717;cfg.id.product=0x3653;cfg.id.version=1;
        strcpy(cfg.name,"Sheng THP Compat Touchscreen");
        if(ioctl(fd_,UI_DEV_SETUP,&cfg)<0)return false;
        for(auto item:std::array<std::pair<unsigned,int>,6>{{{ABS_MT_SLOT,11},{ABS_MT_TRACKING_ID,65535},{ABS_MT_POSITION_X,30479},{ABS_MT_POSITION_Y,20319},{ABS_MT_PRESSURE,1000},{ABS_MT_TOUCH_MAJOR,256}}}){
            uinput_abs_setup axis{};axis.code=item.first;axis.absinfo.maximum=item.second;
            if(item.first==ABS_MT_POSITION_X||item.first==ABS_MT_POSITION_Y)axis.absinfo.resolution=113;
            if(ioctl(fd_,UI_ABS_SETUP,&axis)<0)return false;
        }
        return ioctl(fd_,UI_DEV_CREATE)==0;
    }
    bool report(const std::vector<nvt::Slot>&slots){
        std::array<input_event,nvt::kFingerSlots*8+3> events{};size_t count=0;
        auto emit=[&](uint16_t type,uint16_t code,int value){auto&e=events[count++];e.type=type;e.code=code;e.value=value;};
        std::array<const nvt::Slot*,nvt::kFingerSlots> visible{};
        for(const auto&s:slots)if(s.number>=0&&s.number<nvt::kFingerSlots)visible[s.number]=&s;
        for(int n=0;n<nvt::kFingerSlots;n++){
            if(!visible[n]){if(active_[n]>=0){emit(EV_ABS,ABS_MT_SLOT,n);emit(EV_ABS,ABS_MT_TRACKING_ID,-1);active_[n]=-1;}continue;}
            auto&s=*visible[n];emit(EV_ABS,ABS_MT_SLOT,n);
            if(active_[n]!=s.tracking_id){emit(EV_ABS,ABS_MT_TRACKING_ID,s.tracking_id);active_[n]=s.tracking_id;}
            emit(EV_ABS,ABS_MT_POSITION_X,std::clamp(s.contact.x,0,30479));
            emit(EV_ABS,ABS_MT_POSITION_Y,20319-std::clamp(s.contact.y,0,20319));
            emit(EV_ABS,ABS_MT_TOUCH_MAJOR,std::min(255,s.contact.area));emit(EV_ABS,ABS_MT_PRESSURE,1);
        }
        emit(EV_KEY,BTN_TOUCH,slots.empty()?0:1);emit(EV_KEY,BTN_TOOL_FINGER,slots.empty()?0:1);emit(EV_SYN,SYN_REPORT,0);
        return write(fd_,events.data(),count*sizeof(input_event))==ssize_t(count*sizeof(input_event));
    }
    ~TouchOutput(){if(fd_>=0){report({});ioctl(fd_,UI_DEV_DESTROY);close(fd_);}}
};

class Adapter {
    nvt::TouchCore core_;nvt::FingerFilter filter_;std::vector<nvt::Matrix> samples_;
public:
    std::vector<nvt::Slot> feed(const uint8_t*raw,uint64_t timestamp){
        unsigned type=raw[24];if(type!=2&&type!=4)return {};
        nvt::Matrix matrix{};for(int i=0;i<nvt::kNodes;i++)matrix[i]=int16_t(le16(raw+64+i*2));
        uint16_t counter=le16(raw+2);
        if(!core_.hasReference()){
            if(type==2){core_.process(matrix,counter,2);samples_.clear();puts("THP_REFERENCE_READY source=controller");return {};}
            samples_.push_back(matrix);if(samples_.size()<72)return {};
            nvt::Matrix ref{};std::array<int,72> values{};
            for(int node=0;node<nvt::kNodes;node++){
                for(size_t i=0;i<72;i++)values[i]=samples_[i][node];
                std::sort(values.begin(),values.end());ref[node]=(values[35]+values[36])/2;
            }
            core_.process(ref,counter,2);samples_.clear();puts("THP_REFERENCE_READY source=median72");return {};
        }
        auto result=core_.process(matrix,counter,type);std::vector<nvt::Slot> visible;
        std::array<const nvt::TrackedSlot*,nvt::kFingerSlots> tracked{};
        for(const auto&s:result.tracked_slots)tracked[s.number]=&s;
        for(int n=0;n<nvt::kFingerSlots;n++){
            auto*s=tracked[n];if(!s){filter_.processPipeline(n,0,{},{},timestamp);continue;}
            nvt::FingerCoordinate p{s->contact.y,s->contact.x};
            auto f=filter_.processPipeline(n,s->status,p,p,timestamp,s->age==1);
            if(s->age<2)continue;
            auto contact=s->contact;contact.x=f.coordinate.y;contact.y=f.coordinate.x;
            visible.push_back(nvt::Slot{n,s->tracking_id,std::move(contact)});
        }
        return visible;
    }
};

int main(int argc,char**argv){
    const bool service=argc==2&&!strcmp(argv[1],"--service");
    int seconds=service?0:(argc>1?atoi(argv[1]):300);if(!service&&(seconds<1||seconds>1800))return 2;
    bool dry=argc>2&&!strcmp(argv[2],"--dry-run");setvbuf(stdout,nullptr,_IOLBF,0);
    signal(SIGTERM,stop);signal(SIGINT,stop);
    int lock=open("/data/local/tmp/sheng-thp-bridge.lock",O_CREAT|O_RDWR|O_CLOEXEC,0600);
    if(lock<0||flock(lock,LOCK_EX|LOCK_NB)){perror("touch bridge already running or lock failed");return 10;}
    int fd=open("/dev/xiaomi-touch",O_RDONLY|O_NONBLOCK|O_CLOEXEC);if(fd<0){perror("touch open");return 3;}
    uint8_t p[214]{};
    if(ioctl(fd,_IO('T',3),0UL)<0||ioctl(fd,_IOR('T',1,uint8_t[214]),p)<0){perror("panel parameters");return 4;}
    size_t stride=size_t(p[9])*4096,count=p[10],length=stride*count;
    if(stride<5184||stride>65536||count<2||count>64||length>1048576||le16(p+4)!=40||le16(p+6)!=60)return 5;
    if(ioctl(fd,_IO('T',2),1UL)<0)return 6;
    auto*map=static_cast<const uint8_t*>(mmap(nullptr,length,PROT_READ,MAP_SHARED,fd,0));
    if(map==MAP_FAILED){perror("raw mmap");return 7;}
    TouchOutput output;if(!dry&&!output.setup()){perror("uinput setup");return 8;}
    printf("THP_BRIDGE_READY stride=%zu count=%zu dry=%d matrix_offset=88 axes=30479x20319\n",stride,count,dry);
    Adapter adapter;unsigned frames=0,bad=0,touchframes=0;int lastcontacts=0;
    double end=now()+seconds,last=now();std::array<uint8_t,5184> frame{};
    while(running&&(service||now()<end)){
        pollfd event{fd,POLLIN|POLLRDNORM,0};poll(&event,1,20);
        int index=ioctl(fd,_IO('T',4),0UL);
        if(index<0){
            if(lastcontacts&&now()-last>0.1){if(!dry&&!output.report({}))break;lastcontacts=0;puts("THP_STALL_RELEASE");}
            usleep(1000);continue;
        }
        if(size_t(index)>=count){bad++;continue;}
        memcpy(frame.data(),map+size_t(index)*stride,frame.size());
        auto*raw=frame.data()+24;
        if(raw[0]!=0xa5||raw[1]!=0x5c){bad++;continue;}
        uint64_t timestamp=0;memcpy(&timestamp,frame.data(),8);
        auto slots=adapter.feed(raw,timestamp);int contacts=int(slots.size());
        if(contacts)touchframes++;
        if(contacts!=lastcontacts||((frames%30)==0&&contacts)){
            printf("THP_CONTACTS frame=%u count=%d",frames,contacts);
            for(const auto&s:slots)printf(" slot=%d id=%d x=%d y=%d",s.number,s.tracking_id,s.contact.x,20319-s.contact.y);
            puts("");
        }
        if(!dry&&!output.report(slots)){perror("uinput report");break;}
        lastcontacts=contacts;last=now();frames++;
        if(frames%1200==0)printf("THP_ALIVE frames=%u bad=%u touchframes=%u\n",frames,bad,touchframes);
    }
    printf("THP_BRIDGE_END frames=%u bad=%u touchframes=%u\n",frames,bad,touchframes);
    munmap((void*)map,length);close(fd);close(lock);return frames?0:9;
}
