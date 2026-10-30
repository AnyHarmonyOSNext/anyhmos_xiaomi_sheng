"""Route original HDI passthrough discovery through a RAM compatibility directory."""
from pathlib import Path
import base64
import hashlib
import json

r = Path(__file__).resolve().parent.parent
source = r / 'work/donor-hdi-link/libhdi_base.z.so'
b = source.read_bytes()
old, new = b'/vendor/lib64/passthrough\0', b'/compat/lib64/hdi\0'
assert b.count(old) == 1 and len(new) < len(old)
offset = b.index(old)
replacement = new.ljust(len(old), b'\0')
out = b[:offset]+replacement+b[offset+len(old):]
sha = lambda x: hashlib.sha256(x).hexdigest()
dest = r / 'work/libhdi_base.mapper-compat.z.so'
dest.write_bytes(out)
report = dict(input_sha256=sha(b), output_sha256=sha(out), offset=offset,
              before=old.hex(), after=replacement.hex(), vendor_modified=False,
              purpose='Keep original HDI version selection; mirror vendor passthrough names in /compat; regular mapper copies resolve the compatible linear VDI')
(r / 'analysis/mapper-compat-patch.json').write_text(json.dumps(report, indent=2)+'\n')
lines = ['set -e', 'B=/busybox', 'R=/hmos-root',
         'test ! -e $R/compat/lib64/libhdi_base.z.so',
         f'echo "{sha(b)}  $R/system/lib64/chipset-sdk-sp/libhdi_base.z.so" | $B sha256sum -c -',
         '$B mkdir -p $R/compat/lib64/hdi',
         'for p in $R/vendor/lib64/passthrough/*.so; do',
         ' name=${p##*/}; $B ln -s /vendor/lib64/passthrough/$name $R/compat/lib64/hdi/$name',
         'done']
for v in ['1.0', '1.3']:
    name = f'libmapper_service_{v}.z.so'
    src = r / 'work/mapper-input/vendor/lib64/passthrough' / name
    data = src.read_bytes()
    lines += [f'echo "{sha(data)}  $R/vendor/lib64/passthrough/{name}" | $B sha256sum -c -',
              f'$B rm $R/compat/lib64/hdi/{name}',
              f'$B cp $R/vendor/lib64/passthrough/{name} $R/compat/lib64/hdi/{name}']
lines += ['$B cp $R/system/lib64/chipset-sdk-sp/libhdi_base.z.so $R/compat/lib64/libhdi_base.z.so',
          f"echo '{base64.b64encode(replacement).decode()}' | $B base64 -d | $B dd of=$R/compat/lib64/libhdi_base.z.so bs=1 seek={offset} conv=notrunc",
          f'echo "{sha(out)}  $R/compat/lib64/libhdi_base.z.so" | $B sha256sum -c -',
          '$B chmod 0644 $R/compat/lib64/libhdi_base.z.so',
          '$B mount --bind $R/compat/lib64/libhdi_base.z.so $R/system/lib64/chipset-sdk-sp/libhdi_base.z.so',
          'echo MAPPER_COMPAT_DISCOVERY_RAM_OK']
(r / 'output/apply-mapper-compat-ram.sh').write_text('\n'.join(lines)+'\n', newline='\n')
print(json.dumps(report, indent=2))
