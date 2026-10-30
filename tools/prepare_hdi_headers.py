"""Generate official, unmodified HDI 1.0..1.3 composer client headers."""
from pathlib import Path
import subprocess
base=Path('/root/hmos-work/graphics-deps')
source=base/'source/drivers_interface'
for minor in range(4):
    for file in sorted((source/f'display/composer/v1_{minor}').glob('*.idl')):
        subprocess.run([str(base/'hdi-gen'),'-s','full','-m','ipc','-l','cpp','-r',f'ohos.hdi:{source}','-c',str(file),'-d',str(base/'hdi-generated')],check=True)
print('Generated',len(list((base/'hdi-generated').rglob('*.h'))),'headers')
