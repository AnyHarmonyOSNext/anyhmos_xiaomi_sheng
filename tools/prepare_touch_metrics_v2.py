"""Freeze the working touch path; add bounded aggregate timing only."""
from pathlib import Path
r=Path(__file__).resolve().parent.parent
s=(r/'tools/sheng_thp_bridge.cpp').read_text(encoding='utf-8')
s=s.replace('static uint16_t le16(','''static uint64_t monotonic_ns(){timespec t{};clock_gettime(CLOCK_MONOTONIC,&t);return uint64_t(t.tv_sec)*1000000000ULL+t.tv_nsec;}
struct TouchTiming {
 uint64_t begin=0,n=0,active=0,age_n=0,age_sum=0,age_max=0,process_sum=0,process_max=0,last_raw=0,raw_gap_sum=0,raw_gap_n=0,raw_gap_max=0;
 void record(uint64_t raw,uint64_t start,uint64_t end,bool touch){
  if(!begin)begin=start;++n;if(touch)++active;
  if(start>=raw&&start-raw<5000000000ULL){uint64_t age=start-raw;age_sum+=age;++age_n;if(age>age_max)age_max=age;}
  if(last_raw&&raw>last_raw&&raw-last_raw<1000000000ULL){uint64_t gap=raw-last_raw;raw_gap_sum+=gap;++raw_gap_n;if(gap>raw_gap_max)raw_gap_max=gap;}
  last_raw=raw;process_sum+=end-start;if(end-start>process_max)process_max=end-start;
  if(end-begin<2000000000ULL)return;
  printf("THP_TIMING frames=%llu span_ms=%llu active=%llu raw_gap_n=%llu raw_gap_mean_us=%llu raw_gap_max_us=%llu age_valid=%llu age_mean_us=%llu age_max_us=%llu process_mean_us=%llu process_max_us=%llu raw_ns=%llu now_ns=%llu\\n",
   (unsigned long long)n,(unsigned long long)((end-begin)/1000000),(unsigned long long)active,
   (unsigned long long)raw_gap_n,(unsigned long long)(raw_gap_n?raw_gap_sum/raw_gap_n/1000:0),(unsigned long long)(raw_gap_max/1000),
   (unsigned long long)age_n,(unsigned long long)(age_n?age_sum/age_n/1000:0),(unsigned long long)(age_max/1000),
   (unsigned long long)(process_sum/n/1000),(unsigned long long)(process_max/1000),(unsigned long long)raw,(unsigned long long)start);
  uint64_t previous=last_raw;*this={};last_raw=previous;
 }
};
static uint16_t le16(''')
s=s.replace('    Adapter adapter;unsigned frames=0,bad=0,touchframes=0;int lastcontacts=0;',
            '    Adapter adapter;TouchTiming timing;unsigned frames=0,bad=0,touchframes=0;int lastcontacts=0;')
s=s.replace('        memcpy(frame.data(),map+size_t(index)*stride,frame.size());',
            '        uint64_t process_start=monotonic_ns();\n        memcpy(frame.data(),map+size_t(index)*stride,frame.size());')
s=s.replace('        lastcontacts=contacts;last=now();frames++;',
            '        timing.record(timestamp,process_start,monotonic_ns(),contacts!=0);\n        lastcontacts=contacts;last=now();frames++;')
(r/'tools/sheng_thp_bridge_v2.cpp').write_text(s,encoding='utf-8',newline='\n')
s=(r/'tools/build_sheng_thp.py').read_text(encoding='utf-8').replace("'service-v1'","'service-v2'").replace("'tools/sheng_thp_bridge.cpp'","'tools/sheng_thp_bridge_v2.cpp'")
(r/'tools/build_sheng_thp_v2.py').write_text(s,encoding='utf-8',newline='\n')
print('THP v2 instrumentation staged; original filtering unchanged')
