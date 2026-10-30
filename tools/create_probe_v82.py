"""Integrate the callback receiver that passed the donor's real sync callback."""
from pathlib import Path
import hashlib, shutil
r=Path(__file__).resolve().parents[1]
d=r/'compat/sheng-graphics/v82'
assert not d.exists()
shutil.copytree(r/'compat/sheng-graphics/v81',d)
for p in list(d.iterdir()):
    if not p.is_file() or p.suffix!='.sh':continue
    s=p.read_text(encoding='utf-8').replace('v81','v82').replace('V81','V82')
    name=p.name.replace('v81','v82')
    if name!=p.name:p.unlink()
    (d/name).write_text(s,encoding='utf-8',newline='\n')
for stem,suffix in [('hmos_probe','.c'),('probe_graphics','.inc'),('probe_command','.inc')]:
    s=(r/f'tools/{stem}_v81{suffix}').read_text(encoding='utf-8').replace('v81','v82')
    (r/f'tools/{stem}_v82{suffix}').write_text(s,encoding='utf-8',newline='\n')
shutil.copy2(r/'tools/configs/init-core-v81.cfg',r/'tools/configs/init-core-v82.cfg')
for stem in ['build_probe','verify']:
    s=(r/f'tools/{stem}_v81.py').read_text(encoding='utf-8').replace('v81','v82')
    s=s.replace('debug-tools/native_screenlock_request_v3','debug-tools/native_screenlock_request_v5')
    (r/f'tools/{stem}_v82.py').write_text(s,encoding='utf-8',newline='\n')
old=hashlib.sha256((d/'native_screenlock_request').read_bytes()).hexdigest()
shutil.copy2(r/'compat/debug-tools/native_screenlock_request_v5',d/'native_screenlock_request')
new=hashlib.sha256((d/'native_screenlock_request').read_bytes()).hexdigest()
p=d/'apply-runtime-v82.sh'
s=p.read_text(encoding='utf-8').replace(old,new)
s=s.replace('$B mkdir -p $R/data/local/tmp/sheng-capture', '''$B mkdir -p $R/data/local/tmp/sheng-capture
$B rm -f $R/data/local/tmp/sheng-capture/screenlock-cycle-test $R/data/local/tmp/sheng-capture/screenlock-callback-test''')
p.write_text(s,encoding='utf-8',newline='\n')
shutil.copy2(d/'start-native-desktop-v82.sh',r/'tools/start_native_desktop_v82.sh')
print('v82 staged; original-stub callback sha256='+new)
