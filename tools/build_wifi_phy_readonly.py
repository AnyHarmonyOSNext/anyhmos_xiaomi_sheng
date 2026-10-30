from pathlib import Path
import shutil
import subprocess
r=Path('/mnt/c/SHENG_WORKSPACE')
sdk=Path('/root/hmos-work/sdk-6.0.0.47/installed/native')
inc=r/'work/wifi_nl/include'
(inc/'linux').mkdir(parents=True,exist_ok=True)
shutil.copy2('/root/hmos-work/gki-sheng-exports/include/uapi/linux/nl80211.h',inc/'linux/nl80211.h')
out=r/'compat/debug-tools/wifi_phy_readonly'
subprocess.run([str(sdk/'llvm/bin/clang'),'--target=aarch64-linux-ohos','-std=gnu11','-O2','-Wall','-Wextra','-Werror','-I'+str(inc),str(r/'tools/wifi_phy_readonly.c'),'-o',str(out)],check=True)
subprocess.run([str(sdk/'llvm/bin/llvm-strip'),str(out)],check=True)
print(out.stat().st_size)
