"""Run preload installation as a system installer, not a restricted shell caller."""
from pathlib import Path
import json
import shutil

r = Path(__file__).resolve().parent.parent
d = r / 'compat/sheng-graphics/v97'
assert not d.exists()
shutil.copytree(r / 'compat/sheng-graphics/v96', d)
for p in list(d.iterdir()):
    if p.is_file() and p.suffix in {'.sh', '.cfg'}:
        q = p.with_name(p.name.replace('v96', 'v97'))
        s = p.read_text(encoding='utf-8').replace('v96', 'v97').replace('V96', 'V97')
        if q != p:
            p.unlink()
        q.write_text(s, encoding='utf-8', newline='\n')
for name in ['hmos_probe_v96.c', 'probe_graphics_v96.inc', 'probe_command_v96.inc',
             'build_probe_v96.py', 'verify_v96.py', 'start_native_desktop_v96.sh']:
    (r / 'tools' / name.replace('v96', 'v97')).write_text(
        (r / 'tools' / name).read_text(encoding='utf-8').replace('v96', 'v97'),
        encoding='utf-8', newline='\n')
(r / 'tools/configs/init-core-v97.cfg').write_text(
    (r / 'tools/configs/init-core-v96.cfg').read_text(encoding='utf-8').replace('v96', 'v97'),
    encoding='utf-8', newline='\n')
shutil.copyfile(r / 'compat/debug-tools/native_bundle_cli_v2', d / 'native_bundle_cli')
p = d / 'init-desktop-services.cfg'
cfg = json.loads(p.read_text())
svc = next(x for x in cfg['services'] if x['name'] == 'sheng_bundle_cli')
svc['uid'] = 'system'
svc['gid'] = ['system']
job = next(x for x in cfg['jobs'] if x['name'] == 'param:sheng-bundle-cli')
job['cmds'] = [cmd.replace('chown shell shell', 'chown system system') for cmd in job['cmds']]
p.write_text(json.dumps(cfg, indent=2), encoding='utf-8', newline='\n')
# Prepare the original audio service with its original identity and permissions.
# It remains disabled until a separate, explicit diagnostic trigger.
p = d / 'init-hardware-v97.cfg'
hardware = json.loads(p.read_text())
original = json.loads((r / 'work/hmos_system/system/system/etc/init/audio_server.cfg').read_text())
audio = next(s for s in original['services'] if s['name'] == 'audio_server')
for key in ['critical', 'writepid', 'jobs']:
    audio.pop(key, None)
audio.update(once=1, sandbox=0, saspawn=False)
audio['env'] = [dict(name='PULSE_STATE_PATH', value='/data/data/.pulse_dir/state'),
                dict(name='PULSE_RUNTIME_PATH', value='/data/data/.pulse_dir/runtime')]
hardware['services'].append(audio)
prep = next(j['cmds'] for j in original['jobs'] if j['name'] == 'post-fs-data')
hardware['jobs'].append(dict(name='param:sheng-audio', condition='sheng.debug.start.audio=true',
    cmds=[c for c in prep if not c.startswith(('restorecon ', 'rm ', 'export '))]))
p.write_text(json.dumps(hardware, indent=2), encoding='utf-8', newline='\n')
p = r / 'tools/verify_v97.py'
s = p.read_text().replace("{'powermgr','media_service','av_session'}", "{'powermgr','media_service','av_session','audio_server'}")
s = s.replace("(root/'compat/debug-tools/native_bundle_cli').read_bytes()", "(root/'compat/debug-tools/native_bundle_cli_v2').read_bytes()")
s = s.replace("assert b'apply-preload.sh' in binary", """assert next(x for x in extra['services'] if x['name']=='sheng_bundle_cli')['uid']=='system'
 assert next(x for x in hardware['services'] if x['name']=='audio_server')['uid']=='audio'
 assert b'apply-preload.sh' in binary""")
p.write_text(s, encoding='utf-8', newline='\n')
print('v97 staged: native system preload installer; audio remains opt-in, no vendor changes')
