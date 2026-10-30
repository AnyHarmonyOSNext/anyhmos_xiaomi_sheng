"""Generate unmodified upstream Bluetooth HCI HDI C++ headers."""
from pathlib import Path
import subprocess
b=Path('/root/hmos-work/graphics-deps')
s=b/'source/drivers_interface'
out=b/'bluetooth-hdi-generated'
for p in sorted((s/'bluetooth/hci/v1_0').glob('*.idl')):
    subprocess.run([str(b/'hdi-gen'),'-s','full','-m','ipc','-l','cpp',
        '-r',f'ohos.hdi:{s}','-c',str(p),'-d',str(out)],check=True,stdout=subprocess.DEVNULL)
print('Generated Bluetooth headers:',len(list(out.rglob('*.h'))))
