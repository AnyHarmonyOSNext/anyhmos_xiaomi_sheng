"""Use the validated host's actual readiness deadlines, not attempt counts."""
from pathlib import Path
import shutil
r=Path(__file__).resolve().parents[1]
d=r/'compat/sheng-graphics/v81'
assert not d.exists()
shutil.copytree(r/'compat/sheng-graphics/v80',d)
for p in list(d.iterdir()):
    if not p.is_file() or p.suffix!='.sh':continue
    s=p.read_text(encoding='utf-8').replace('v80','v81').replace('V80','V81')
    name=p.name.replace('v80','v81')
    if name!=p.name:p.unlink()
    (d/name).write_text(s,encoding='utf-8',newline='\n')
for stem,suffix in [('hmos_probe','.c'),('probe_graphics','.inc'),('probe_command','.inc')]:
    s=(r/f'tools/{stem}_v80{suffix}').read_text(encoding='utf-8').replace('v80','v81')
    if stem=='hmos_probe':
        s=s.replace('"timeout","300"','"timeout","600"').replace('bounded=300s','bounded=600s')
    (r/f'tools/{stem}_v81{suffix}').write_text(s,encoding='utf-8',newline='\n')
shutil.copy2(r/'tools/configs/init-core-v80.cfg',r/'tools/configs/init-core-v81.cfg')
for stem in ['build_probe','verify']:
    s=(r/f'tools/{stem}_v80.py').read_text(encoding='utf-8').replace('v80','v81')
    (r/f'tools/{stem}_v81.py').write_text(s,encoding='utf-8',newline='\n')
p=d/'start-native-desktop-v81.sh'
s=p.read_text(encoding='utf-8')
s=s.replace('stage=prepare', '''stage=prepare
now() { read seconds rest < /proc/uptime; echo "${seconds%.*}"; }''',1)
s=s.replace('stage=database\ni=0', 'stage=database\ndeadline=$(($(now)+90))\ni=0')
s=s.replace('i=$((i+1)); [ "$i" -lt 24 ] || exit 22;', 'i=$((i+1)); [ "$(now)" -lt "$deadline" ] || exit 22;')
s=s.replace('i=0\nwhile :; do\n path=', 'deadline=$(($(now)+120))\ni=0\nwhile :; do\n path=')
s=s.replace('i=$((i+1)); [ "$i" -lt 30 ] || exit 32;', 'i=$((i+1)); [ "$(now)" -lt "$deadline" ] || exit 32;')
p.write_text(s,encoding='utf-8',newline='\n')
shutil.copy2(p,r/'tools/start_native_desktop_v81.sh')
print('v81 staged with monotonic database90s/scene120s deadlines, overall600s')
