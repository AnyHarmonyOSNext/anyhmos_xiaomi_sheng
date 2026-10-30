from pathlib import Path
from verify_probe import parse
new=parse(Path('work/trace_verify/ramdisk.cpio').read_bytes());old=parse(Path('work/stock_init_boot/ramdisk.cpio').read_bytes())
assert new['init'][1]==Path('work/hmos_trace').read_bytes();assert new['init.android.original'][1]==old['init'][1]
for k,v in old.items():
 if k not in ['init','TRAILER!!!']:assert new[k]==v,k
print('TRACE cpio verified')
