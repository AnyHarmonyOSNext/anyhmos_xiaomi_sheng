"""WSL: inspect donor WLAN dependency and transport evidence without loading it."""
from pathlib import Path
import re
import subprocess

r = Path(__file__).resolve().parent.parent
for name in ['libwifi_hal_hw.z.so', 'libhdi_wlan_impl.z.so', 'libwpa.z.so',
             'libwifi_hdi_c_device.z.so', 'libwpa_hdi_c_device.z.so',
             'libwlan_interface_service_1.3.z.so']:
    p = r / 'work/wifi-offline/vendor/lib64' / name
    assert p.read_bytes()[:4] == b'\x7fELF', p
    print('LIBRARY=' + name)
    dynamic = subprocess.check_output(['aarch64-linux-gnu-readelf', '-d', str(p)], text=True)
    print('\n'.join(s for s in dynamic.splitlines() if 'NEEDED' in s))
    strings = subprocess.check_output(['aarch64-linux-gnu-strings', str(p)], text=True)
    print('\n'.join(s for s in strings.splitlines()
                    if re.search(r'nl80211|hisi|wal_|/dev/|wlan0|/sys/|GetInstance|Hdi.*Impl', s, re.I))[:4000])
