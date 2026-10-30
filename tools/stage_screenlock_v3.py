from pathlib import Path
import hashlib, shutil
r=Path(__file__).resolve().parents[1]
s=(r/'tools/native_screenlock_request_v2.cpp').read_text(encoding='utf-8')
s=s.replace('#include <unistd.h>','#include <unistd.h>\n#include <pthread.h>\n#include "ipc_skeleton.h"')
s=s.replace('    sptr<Callback> callback = new Callback;', '''    if (!IPCSkeleton::SetMaxWorkThreadNum(2)) return 7;
    pthread_t ipcThread;
    if (pthread_create(&ipcThread, nullptr, [](void*) -> void* {
        IPCSkeleton::JoinWorkThread(); return nullptr;
    }, nullptr) != 0) return 8;
    pthread_detach(ipcThread);
    sptr<Callback> callback = new Callback;''')
(r/'tools/native_screenlock_request_v3.cpp').write_text(s,encoding='utf-8',newline='\n')
s=(r/'tools/build_screenlock_request_v2.py').read_text(encoding='utf-8').replace('v2','v3')
(r/'tools/build_screenlock_request_v3.py').write_text(s,encoding='utf-8',newline='\n')
print('v3 source staged; build then run this script with --install')
import sys
if '--install' in sys.argv:
    d=r/'compat/sheng-graphics/v80'
    old=hashlib.sha256((d/'native_screenlock_request').read_bytes()).hexdigest()
    shutil.copy2(r/'compat/debug-tools/native_screenlock_request_v3',d/'native_screenlock_request')
    new=hashlib.sha256((d/'native_screenlock_request').read_bytes()).hexdigest()
    p=d/'apply-runtime-v80.sh'
    p.write_text(p.read_text(encoding='utf-8').replace(old,new),encoding='utf-8',newline='\n')
    p=r/'tools/verify_v80.py'
    p.write_text(p.read_text(encoding='utf-8').replace('debug-tools/native_screenlock_request_v2','debug-tools/native_screenlock_request_v3'),encoding='utf-8',newline='\n')
    print('v3 installed into unflashed v80; rebuild required; sha256='+new)
