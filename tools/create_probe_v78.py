"""Freeze v77 and stage the runtime fixes that passed real desktop validation."""
from pathlib import Path
import base64, gzip, hashlib, json, shutil
r=Path(__file__).resolve().parents[1]
d=r/'compat/sheng-graphics/v78';assert not d.exists()
shutil.copytree(r/'compat/sheng-graphics/v77',d)
for name in ['hmos_probe.c','probe_graphics.inc','probe_command.inc']:
    old=r/'tools'/name
    archived=r/'tools/archive'/(old.stem+'_v77'+old.suffix)
    if not archived.exists():shutil.copy2(old,archived)
    new=r/'tools'/(old.stem+'_v78'+old.suffix)
    assert not new.exists();new.write_text(old.read_text().replace('v77','v78'),newline='\n')
p=r/'tools/hmos_probe_v78.c'
p.write_text(p.read_text().replace('"probe_graphics.inc"','"probe_graphics_v78.inc"').replace('"probe_command.inc"','"probe_command_v78.inc"'),newline='\n')
for src,name in [
    ('compat/sheng-graphics/surface-post-v2/libsheng_surface_diagnostic.so','libsheng_surface_diagnostic.so'),
    ('compat/sheng-touch/service-v1/sheng_thp_bridge','sheng_thp_bridge'),
    ('compat/debug-tools/native_thp_launcher','native_thp_launcher'),
    ('compat/debug-tools/native_screenlock_request','native_screenlock_request'),
    ('compat/debug-tools/native_debug_dispatch_v2','native_input_dispatch')]:
    shutil.copy2(r/src,d/name)
driver=(r/'compat/sheng-graphics/blob-import-v1/libvulkan_freedreno.so').read_bytes()
driver_sha=hashlib.sha256(driver).hexdigest()
assert driver_sha=='5064973ec0fc7300fbbab9da5b7b1967fe18f5594315a32a7eac8ce82299be6e'
(d/'libvulkan_freedreno.so.gz').write_bytes(gzip.compress(driver,compresslevel=9,mtime=0))
p=d/'apply-compat-paths.sh';s=p.read_text()
assert s.count('ad70f97f37dfc511e999f4dcbe8a249ca06a9cb24869e09c6284a64729845955')==1
p.write_text(s.replace('ad70f97f37dfc511e999f4dcbe8a249ca06a9cb24869e09c6284a64729845955',driver_sha),newline='\n')
usage='''set -e
B=/busybox
R=/hmos-root
p=$R/compat/lib64/librender_service_base.z.so
echo "d423413ec1fc58f40c5b04846b00530a4d82d0929eee769ede3bf5c605e5a77d  $p" | $B sha256sum -c -
echo 6QKAUg== | $B base64 -d | $B dd of="$p" bs=1 seek=9162080 conv=notrunc
echo "7f4fdf74cc0897ed322af94835a76fa3f5dd8fa82f44f75f5ab47cfa7a91f57b  $p" | $B sha256sum -c -
echo SHENG_RGB_RENDERABLE_USAGE_INSTALLED
'''
assert base64.b64decode('6QKAUg==').hex()=='e9028052'
(d/'apply-render-usage.sh').write_text(usage,newline='\n')
(d/'oobe_page_offline.json').write_text(json.dumps([
    dict(key='wlan',action='delete'),dict(key='activation_lock',action='delete'),
    dict(key='account_login',action='delete')],indent=2)+'\n',newline='\n')
stage=['set -e','B=/busybox','R=/hmos-root']
for name in ['sheng_thp_bridge','native_thp_launcher','native_screenlock_request']:
    sha=hashlib.sha256((d/name).read_bytes()).hexdigest()
    stage += [f'$B cp /graphics/{name} $R/compat/bin/{name}',f'echo "{sha}  $R/compat/bin/{name}" | $B sha256sum -c -',f'$B chmod 0755 $R/compat/bin/{name}']
stage += [
 ': > $R/data/local/tmp/sheng-thp-service.txt',
 '$B mkdir -p $R/data/local/tmp/sheng-capture',
 ': > $R/data/local/tmp/sheng-capture/unlock-request.txt',
 '$B chown 2000:2000 $R/data/local/tmp/sheng-capture/unlock-request.txt',
 '$B touch $R/data/local/tmp/sheng-gpu-owner-cleanup',
 '$B chmod 0644 $R/data/local/tmp/sheng-gpu-owner-cleanup',
 '$B mkdir -p $R/compat/oobe-offline-v1',
 '$B cp $R/sys_prod/etc/oobe/hwupgrade_extend_pages.json $R/compat/oobe-offline-v1/hwupgrade_extend_pages.json',
 '$B cp /graphics/oobe_page_offline.json $R/compat/oobe-offline-v1/oobe_page.json',
 '$B chmod 0755 $R/compat/oobe-offline-v1',
 '$B chmod 0644 $R/compat/oobe-offline-v1/*.json',
 '$B mount --bind $R/compat/oobe-offline-v1 $R/sys_prod/etc/oobe',
 'for name in xiaomi-touch uinput; do',
 ' nums=$($B cat /sys/class/misc/$name/dev)',
 ' $B test ! -e $R/dev/$name',
 ' $B mknod $R/dev/$name c "${nums%:*}" "${nums#*:}"',
 ' $B chmod 0600 $R/dev/$name',
 'done',
 '$B test -f /proc/xm_htc_report_coordinate',
 'echo 0 > /proc/xm_htc_report_coordinate',
 'echo SHENG_V78_RUNTIME_STAGED_VENDOR_UNTOUCHED']
(d/'apply-runtime-v78.sh').write_text('\n'.join(stage)+'\n',newline='\n')
p=r/'tools/probe_graphics_v78.inc';s=p.read_text()
marker='    if(graphics_run_script("/graphics/apply-framework-dev.sh")<0)return -1;'
assert s.count(marker)==1
s=s.replace(marker,'    if(graphics_run_script("/graphics/apply-render-usage.sh")<0)return -1;\n'+marker)
marker='    if(graphics_run_script("/graphics/apply-touch.sh")<0)return -1;'
assert s.count(marker)==1
s=s.replace(marker,marker+'\n    if(graphics_run_script("/graphics/apply-runtime-v78.sh")<0)return -1;')
p.write_text(s,newline='\n')
extra=json.loads((d/'init-desktop-services.cfg').read_text())
extra['services'] += [
 dict(name='sheng_touch_bridge',path=['/compat/bin/native_thp_launcher'],uid='root',gid=['root','input'],
      caps=['MKNOD','CHOWN','DAC_OVERRIDE','FOWNER'],disabled=1,once=1,sandbox=0,saspawn=False,**{'start-mode':'condition'}),
 dict(name='sheng_screen_unlock',path=['/compat/bin/native_screenlock_request'],uid='shell',gid=['shell'],apl='system_core',
      permission=['ohos.permission.ACCESS_SCREEN_LOCK'],disabled=1,once=1,sandbox=0,saspawn=False,**{'start-mode':'condition'})]
extra['jobs'] += [
 dict(name='param:sheng-touch-bridge',condition='sheng.debug.start.touch=true',cmds=['start sheng_touch_bridge']),
 dict(name='param:sheng-screen-unlock',condition='sheng.debug.screen.unlock=true',cmds=[
      'mkdir /data/local/tmp/sheng-capture 0755 shell shell','start sheng_screen_unlock'])]
(d/'init-desktop-services.cfg').write_text(json.dumps(extra,indent=2)+'\n',newline='\n')
shutil.copy2(r/'tools/configs/init-core-v77.cfg',r/'tools/configs/init-core-v78.cfg')
for name in ['build_probe','verify']:
    s=(r/f'tools/{name}_v77.py').read_text(encoding='utf-8').replace('v77','v78')
    s=s.replace('tools/hmos_probe.c','tools/hmos_probe_v78.c').replace('tools/probe_graphics.inc','tools/probe_graphics_v78.inc').replace('tools/probe_command.inc','tools/probe_command_v78.inc')
    if name=='verify':
        s=s.replace('sheng-graphics/surface-diagnostic-v1/','sheng-graphics/surface-post-v2/')
        s=s.replace('sheng-graphics/gpu-diagnostic-v1/','sheng-graphics/blob-import-v1/')
        s=s.replace("'sheng_input_dispatch','compatibility_config_center'}", "'sheng_input_dispatch','compatibility_config_center','sheng_touch_bridge','sheng_screen_unlock'}")
        marker=" assert binary[:4]==b'\\x7fELF'"
        assert s.count(marker)==1
        assertions=''' assert new['graphics/sheng_thp_bridge'][1]==(root/'compat/sheng-touch/service-v1/sheng_thp_bridge').read_bytes()
 assert new['graphics/native_input_dispatch'][1]==(root/'compat/debug-tools/native_debug_dispatch_v2').read_bytes()
 assert new['graphics/native_thp_launcher'][1]==(root/'compat/debug-tools/native_thp_launcher').read_bytes()
 assert new['graphics/native_screenlock_request'][1]==(root/'compat/debug-tools/native_screenlock_request').read_bytes()
 assert b'apply-render-usage.sh' in binary and b'apply-runtime-v78.sh' in binary
 assert b'seek=9162080' in new['graphics/apply-render-usage.sh'][1]
 assert b'sheng-gpu-owner-cleanup' in new['graphics/apply-runtime-v78.sh'][1]
 assert json.loads(new['graphics/oobe_page_offline.json'][1])==[dict(key=x,action='delete') for x in ['wlan','activation_lock','account_login']]
'''
        s=s.replace(marker,assertions+marker)
    (r/f'tools/{name}_v78.py').write_text(s,encoding='utf-8',newline='\n')
print('v78 staged in separate sources/assets; v77 frozen; not built or flashed')
