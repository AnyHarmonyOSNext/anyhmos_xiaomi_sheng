"""Bundle v46's device-verified firmware lookup correction; no vendor writes."""
from pathlib import Path
import shutil,json
r=Path(__file__).resolve().parent.parent
for name in ['hmos_probe.c','probe_graphics.inc','probe_command.inc']:
    dst=r/'tools/archive'/(Path(name).stem+'_v46'+Path(name).suffix)
    if not dst.exists():shutil.copy2(r/'tools'/name,dst)
shutil.copytree(r/'compat/sheng-graphics/v46',r/'compat/sheng-graphics/v47',dirs_exist_ok=True)
c=(r/'tools/archive/hmos_probe_v46.c').read_text().replace('v46','v47')
(r/'tools/hmos_probe.c').write_text(c)
g=(r/'tools/archive/probe_graphics_v46.inc').read_text()
g=g.replace('put("/sys/module/firmware_class/parameters/path","/hmos-root/compat/firmware")',
            'put("/sys/module/firmware_class/parameters/path","/compat/firmware")')
assert 'put("/sys/module/firmware_class/parameters/path","/compat/firmware")' in g
(r/'tools/probe_graphics.inc').write_text(g)
for a,b in [('build_probe_v46.py','build_probe_v47.py'),('verify_v46.py','verify_v47.py')]:
    (r/'tools'/b).write_text((r/'tools'/a).read_text().replace('v46','v47'))
shutil.copy2(r/'tools/configs/init-core-v46.cfg',r/'tools/configs/init-core-v47.cfg')
report={'version':'v47','status':'OFFLINE_CANDIDATE_NOT_FLASHED',
    'change':'Firmware lookup path must resolve in native caller chroot: /compat/firmware, not host /hmos-root/compat/firmware.',
    'evidence':['output/logs/command-shell-20261027-214517-7116ccc22c13.log',
                'output/logs/command-shell-20261027-214559-2b15d521d2c8.log',
                'output/logs/command-shell-20261027-214736-5e781dae377f.log'],
    'v46_runtime_passed':['vendor/vendor_dlkm EROFS ro, no vendor init mask',
        'original composer SHA unchanged; original HDI loads private VDI from /compat',
        'after runtime firmware path fix, native Rosen 12288 pixels +32 guards passed',
        'real KMS scanout plane90/fb66 3048x2032 captured',
        'original installs UID/permissions started and SA511 Publish result0'],
    'unverified':['v47 cold boot','desktop','default screenshot API','touch','WiFi']}
(r/'analysis/v47-compat-layer.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps(report,indent=2))
