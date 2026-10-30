"""WSL: build a narrow ioctl compatibility layer and an isolated original-HAL probe."""
from pathlib import Path
import hashlib,json,subprocess,shutil
r=Path(__file__).resolve().parent.parent
sdk=Path('/root/hmos-work/sdk-6.0.0.47/installed/native')
inc=r/'work/wifi_nl/include';(inc/'linux').mkdir(parents=True,exist_ok=True)
shutil.copy2('/root/hmos-work/gki-sheng-exports/include/uapi/linux/nl80211.h',inc/'linux/nl80211.h')
out=r/'compat/sheng-wireless/category-v134';out.mkdir(parents=True,exist_ok=True)
flags=[str(sdk/'llvm/bin/clang'),'--target=aarch64-linux-ohos','-std=gnu11',
    '-O2','-Wall','-Wextra','-Werror','-I'+str(inc)]
library=out/'libsheng_wifi_category_v134.so';probe=out/'native_wifi_category_probe_v134'
subprocess.run(flags+['-fPIC','-fvisibility=hidden','-shared',str(r/'tools/wifi_caps_v134.c'),
    str(r/'tools/wifi_category_ioctl_v134.c'),'-Wl,-soname,libsheng_wifi_category_v134.so','-o',str(library)],check=True)
subprocess.run(flags+[str(r/'tools/wifi_caps_v134.c'),str(r/'tools/native_wifi_category_probe_v134.c'),
    '-ldl','-o',str(probe)],check=True)
for p in [library,probe]: subprocess.run([str(sdk/'llvm/bin/llvm-strip'),str(p)],check=True)
report=dict(version='v134',status='built_not_tested',vendor_unchanged=True,
    scope='Exact CMD_WIFI_CATEGORY ioctl only; real target-interface wiphy HE/EHT; failures and all other requests use SYS_ioctl',
    files=[dict(file=p.name,bytes=p.stat().st_size,sha256=hashlib.sha256(p.read_bytes()).hexdigest()) for p in [library,probe]])
(r/'analysis/wifi-category-build-v134.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps(report,indent=2))
