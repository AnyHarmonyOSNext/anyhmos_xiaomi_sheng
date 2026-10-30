"""Freeze v76 and stage tested padding, stock keys, panel identity and surface diagnostics."""
from pathlib import Path
import shutil,json
r=Path(__file__).resolve().parents[1]
d=r/'compat/sheng-graphics/v77'
assert not d.exists()
for name in ['hmos_probe.c','probe_graphics.inc','probe_command.inc']:
    p=r/'tools'/name; frozen=r/'tools/archive'/(p.stem+'_v76'+p.suffix)
    assert not frozen.exists(); shutil.copy2(p,frozen)
shutil.copytree(r/'compat/sheng-graphics/v76',d)
for source,name in [
    ('padding-v1','libdisplay_buffer_vdi_impl.z.so'),
    ('panel-capability-v1','libdisplay_composer_vdi_impl.z.so'),
    ('surface-diagnostic-v1','libsheng_surface_diagnostic.so')]:
    shutil.copy2(r/'compat/sheng-graphics'/source/name,d/name)
touch=d/'apply-touch.sh'
text=touch.read_text()
marker='$B insmod /lib/modules/spi-msm-geni.ko'
assert text.count(marker)==1
text=text.replace(marker, '$B insmod /lib/modules/reboot-mode.ko\n$B insmod /lib/modules/qcom-pon.ko\n'+marker)
touch.write_text(text,newline='\n')
core=json.loads((r/'tools/configs/init-core-v76.cfg').read_text())
service=next(s for s in core['services'] if s['name']=='render_service')
assert 'env' not in service
service['env']=[dict(name='LD_PRELOAD',value='/compat/lib64/libsheng_surface_diagnostic.so')]
(r/'tools/configs/init-core-v77.cfg').write_text(json.dumps(core,indent=2)+'\n')
p=r/'tools/probe_graphics.inc'; text=p.read_text()
marker='    if(copy_ram_asset("/graphics/native_render_launcher"'
# Stage the observer before launching the native render service.
before='    const char *render_logs[]='
assert text.count(before)==1
text=text.replace(before, '    if(copy_ram_asset("/graphics/libsheng_surface_diagnostic.so","/hmos-root/compat/lib64/libsheng_surface_diagnostic.so",0644)<0)return -1;\n'+before)
p.write_text(text)
p=r/'tools/hmos_probe.c';p.write_text(p.read_text().replace('v76','v77'))
for name in ['build_probe','verify']:
    text=(r/f'tools/{name}_v76.py').read_text().replace('v76','v77')
    if name=='verify':
        text=text.replace('sheng-graphics/stride-v1/','sheng-graphics/padding-v1/')
        text=text.replace('sheng-graphics/fence-v1/','sheng-graphics/panel-capability-v1/')
        text=text.replace(" assert b'\\r' not in new['graphics/apply-touch.sh'][1]", " assert b'\\r' not in new['graphics/apply-touch.sh'][1]\n assert b'/lib/modules/qcom-pon.ko' in new['graphics/apply-touch.sh'][1]\n assert new['graphics/libsheng_surface_diagnostic.so'][1]==(root/'compat/sheng-graphics/surface-diagnostic-v1/libsheng_surface_diagnostic.so').read_bytes()")
    (r/f'tools/{name}_v77.py').write_text(text)
print('v77 staged, not flashed')
