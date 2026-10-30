"""Generate the pinned public C WLAN HDI headers for ABI inspection."""
from pathlib import Path
import subprocess

b = Path('/root/hmos-work/graphics-deps')
s = b/'source/drivers_interface'
out = b/'wlan-hdi-generated'
for minor in range(4):
    for p in sorted((s/f'wlan/v1_{minor}').glob('*.idl')):
        subprocess.run([str(b/'hdi-gen'), '-s', 'full', '-m', 'ipc', '-l', 'c',
                        '-r', f'ohos.hdi:{s}', '-c', str(p), '-d', str(out)], check=True,
                        stdout=subprocess.DEVNULL)
print('Generated WLAN HDI headers:', len(list(out.rglob('*.h'))))
