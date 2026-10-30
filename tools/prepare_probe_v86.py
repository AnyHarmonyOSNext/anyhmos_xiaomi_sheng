"""Keep v85 intact; add the actual form service and bounded composer evidence."""
from pathlib import Path
import json
import shutil

r = Path(__file__).resolve().parent.parent
d = r / 'compat/sheng-graphics/v86'
assert not d.exists(), 'v86 already staged'
shutil.copytree(r / 'compat/sheng-graphics/v85', d)
for p in list(d.iterdir()):
    if p.is_file() and p.suffix in {'.sh', '.cfg'}:
        s = p.read_text(encoding='utf-8').replace('v85', 'v86').replace('V85', 'V86')
        dest = p.with_name(p.name.replace('v85', 'v86'))
        if dest != p:
            p.unlink()
        dest.write_text(s, encoding='utf-8', newline='\n')
for name in ['hmos_probe_v85.c', 'probe_graphics_v85.inc', 'probe_command_v85.inc',
             'build_probe_v85.py', 'verify_v85.py', 'start_native_desktop_v85.sh']:
    p = r / 'tools' / name
    p.with_name(name.replace('v85', 'v86')).write_text(
        p.read_text(encoding='utf-8').replace('v85', 'v86'), encoding='utf-8', newline='\n')
p = r / 'tools/configs/init-core-v86.cfg'
p.write_text((r / 'tools/configs/init-core-v85.cfg').read_text(encoding='utf-8').replace('v85', 'v86'),
             encoding='utf-8', newline='\n')
stock = json.loads((r / 'work/hmos_system/system/system/profile/foundation.json').read_text(encoding='utf-8'))
form = next(x for x in stock['systemability'] if x['name'] == 403)
p = d / 'foundation-app-core.json'
c = json.loads(p.read_text(encoding='utf-8'))
assert not any(x['name'] == 403 for x in c['systemability'])
c['systemability'].insert(1, form)
p.write_text(json.dumps(c, indent=2) + '\n', encoding='utf-8', newline='\n')
p = d / 'apply-hardware-v86.sh'
p.write_text(p.read_text(encoding='utf-8') + '''
: > $R/data/local/tmp/sheng-composer-metrics.txt
$B chown 3036:3036 $R/data/local/tmp/sheng-composer-metrics.txt
$B chmod 0640 $R/data/local/tmp/sheng-composer-metrics.txt
''', encoding='utf-8', newline='\n')
print('v86 staged: original SA403, no fake results, bounded per-2s composer metrics')
