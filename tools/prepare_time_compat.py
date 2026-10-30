"""Port the reference's unsupported poweroff-slot idea to this guarded ELF."""
from pathlib import Path
import hashlib
import json

r=Path(__file__).resolve().parent.parent
d=r/'compat/sheng-framework/time-v1'
d.mkdir(exist_ok=True)
p=r/'work/time_service/libtime-original.so'
b=p.read_bytes()
original='aa5383b1cb0201e4b5b87850c80f33bd3e82efda9165d9b0ea122a4618152cf4'
assert hashlib.sha256(b).hexdigest()==original
offset=0x3aef0
before=bytes.fromhex('800180520100815203000014')
# Slot 6 is CLOCK_POWER_OFF_ALARM(12), unsupported on the stock Android kernel.
# Preserve -1 in the slot and continue loop bookkeeping at VA 0x3bfe0.
# Registers/branch differ from the AnyHarmonyOS donor: x19 base, x20 index.
after=bytes.fromhex('00008012607a34b83a000014')
guards={offset-8:'9f1a00f181000054',offset+24:'607a34b8',0x3aff0:'1f1d00f1'}
assert b[offset:offset+12]==before
for off,v in guards.items():assert b[off:off+len(bytes.fromhex(v))]==bytes.fromhex(v),(off,v)
out=b[:offset]+after+b[offset+12:]
digest=hashlib.sha256(out).hexdigest()
(d/'libtime_system_ability.z.so').write_bytes(out)
manifest={'name':'sheng-supported-timerfds','input_sha256':original,'output_sha256':digest,
          'changes':[{'offset':offset,'before':before.hex(),'after':after.hex()}],
          'guards':[{'offset':k,'bytes':v} for k,v in guards.items()],
          'reference':'AnyHarmonyOS/sm8650/framework-patches/supported-timerfds.json',
          'scope':'Preserve six real supported timerfds; unsupported poweroff slot remains -1. No fake fd or clock.',
          'bytes':len(out)}
(d/'patch.json').write_text(json.dumps(manifest,indent=2)+'\n')
octal=''.join('\\%03o'%x for x in after)
script=f'''#!/busybox sh
# Guarded RAM overlay. The system image and vendor remain unchanged.
set -eu
B=/busybox
R=/hmos-root
S=$R/system/lib64/libtime_system_ability.z.so
T=$R/compat/lib64/libtime_system_ability.z.so
sum=$($B sha256sum "$S"); sum=${{sum%% *}}
if [ "$sum" = {digest} ]; then echo TIME_TIMERFDS_RAM_ALREADY_STAGED=1; exit 0; fi
[ "$sum" = {original} ] || exit 61
$B cp "$S" "$T"
$B printf '{octal}' | $B dd of="$T" bs=1 seek={offset} conv=notrunc 2>/dev/null
echo '{digest}  '"$T" | $B sha256sum -c -
$B chmod 0644 "$T"
$B mount --bind "$T" "$S"
echo '{digest}  '"$S" | $B sha256sum -c -
echo TIME_TIMERFDS_RAM_STAGED_SIX_REAL_CLOCKS=1
'''
(d/'apply-time-v1.sh').write_text(script,newline='\n')
print(json.dumps(manifest,indent=2))
