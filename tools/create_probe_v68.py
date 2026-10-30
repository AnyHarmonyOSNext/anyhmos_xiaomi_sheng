"""Bound retries for SceneBoard's verified absent optional SA1154."""
from pathlib import Path
import json
import shutil
import subprocess

r = Path(__file__).resolve().parent.parent
for n in ['hmos_probe.c', 'probe_graphics.inc', 'probe_command.inc']:
    p = r / 'tools' / n
    q = r / 'tools/archive' / (p.stem + '_v67' + p.suffix)
    if not q.exists():
        shutil.copy2(p, q)
d = r / 'compat/sheng-graphics/v68'
assert not d.exists()
shutil.copytree(r / 'compat/sheng-graphics/v67', d)
cfg = json.loads((r / 'tools/configs/init-core-v67.cfg').read_text())
next(x for x in cfg['services'] if x['name'] == 'appspawn')['env'] = [
    {'name': 'LD_PRELOAD', 'value': '/compat/lib64/libsheng_scb_optional_sa.so'}]
(r / 'tools/configs/init-core-v68.cfg').write_text(json.dumps(cfg, indent=2) + '\n')
(d / 'sceneboard-optional-sa.list').write_text('1154\n')
w = '/mnt/c/SHENG_WORKSPACE/'
sdk = json.loads(subprocess.check_output(['wsl','-d','Ubuntu-22.04','--','cat','/root/hmos-work/sdk-6.0.0.47/installation.json'], text=True))['sdk']
subprocess.run(['wsl','-d','Ubuntu-22.04','--',sdk+'/llvm/bin/clang++',
                '--target=aarch64-linux-ohos','-std=c++17','-O2','-Wall','-Wextra','-Werror',
                '-Wno-return-type-c-linkage','-fno-exceptions','-fno-rtti','-nostdlib++',
                '-shared','-fPIC','-Wl,-z,relro,-z,now',
                w+'compat/sheng-framework/persistent-v1/sceneboard_optional_sa.cpp',
                '-o',w+'compat/sheng-graphics/v68/libsheng_scb_optional_sa.so'],check=True)
subprocess.run(['wsl','-d','Ubuntu-22.04','--',sdk+'/llvm/bin/llvm-strip',
                w+'compat/sheng-graphics/v68/libsheng_scb_optional_sa.so'],check=True)
p = r / 'tools/probe_graphics.inc'
s = p.read_text()
mark = '    note("SYSTEM_AUDIO_POLICY_COMPAT_BIND: original nonblocking query for SA3009; vendor untouched");'
assert s.count(mark) == 1
s = s.replace(mark, mark + '\n    if(copy_ram_asset("/graphics/libsheng_scb_optional_sa.so","/hmos-root/compat/lib64/libsheng_scb_optional_sa.so",0644)<0)return -1;\n    if(copy_ram_asset("/graphics/sceneboard-optional-sa.list","/hmos-root/compat/etc/sceneboard-optional-sa.list",0644)<0)return -1;')
p.write_text(s)
p = r / 'tools/hmos_probe.c'
p.write_text(p.read_text().replace('v67', 'v68'))
for n in ['build_probe', 'verify']:
    (r / f'tools/{n}_v68.py').write_text((r / f'tools/{n}_v67.py').read_text().replace('v67', 'v68'))
print('v68: minimal libc/dl bridge, actual CheckSystemAbility preserved, SceneBoard+SA1154 only')
