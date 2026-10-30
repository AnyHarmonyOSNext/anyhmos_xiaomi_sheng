"""WSL: build the OHOS C interface adapter against the upstream public header."""
from pathlib import Path
import subprocess,hashlib,json
r=Path(__file__).resolve().parent.parent
sdk=Path('/root/hmos-work/sdk-6.0.0.47/installed/native')
header=Path('/root/hmos-work/graphics-deps/source/drivers_peripheral/bluetooth/hci/hdi_service/implement')
common=[str(sdk/'llvm/bin/clang++'),'--target=aarch64-linux-ohos','-O2','-Wall','-Wextra','-Werror','-I'+str(header)]
outputs=[]
for src,name,flags in [('bluetooth_vendor_v136.cpp','libbt_vendor_sheng_v136.so',['-fPIC','-shared']),
    ('native_bt_vendor_check_v136.cpp','native_bt_vendor_check_v136',[])]:
    out=r/'output'/name
    subprocess.run(common+flags+[str(r/'tools'/src),'-ldl','-o',str(out)],check=True)
    subprocess.run([str(sdk/'llvm/bin/llvm-strip'),str(out)],check=True)
    outputs.append(dict(file=str(out.relative_to(r)),bytes=out.stat().st_size,sha256=hashlib.sha256(out.read_bytes()).hexdigest()))
(r/'analysis/bluetooth-vendor-v136-build.json').write_text(json.dumps(outputs,indent=2)+'\n',encoding='utf-8')
print(json.dumps(outputs))
