from pathlib import Path
import subprocess,struct,json,sys,hashlib,gzip
version='v92';root=Path.cwd();exe='C:/MIO-KITCHEN-PYSIDE6-5.0.0-PREVIEW/bin/Windows/AMD64/magiskboot.exe'
def parse(b):
 i=0;out={}
 while i+110<=len(b) and b[i:i+6]==b'070701':
  v=[int(b[i+6+j*8:i+14+j*8],16) for j in range(13)];n=b[i+110:i+110+v[11]-1].decode();o=(i+110+v[11]+3)&~3;out[n]=(v,b[o:o+v[6]]);i=(o+v[6]+3)&~3
  if n=='TRAILER!!!':return out
 raise ValueError('No CPIO trailer')
old=parse((root/'work/stock_init_boot/ramdisk.cpio').read_bytes());results={}
for mode in ['probe','trace']:
 image=root/f'output/init_boot_hmos_{mode}_{version}.img';dest=root/f'work/{version}_verify_{mode}';dest.mkdir(exist_ok=True)
 subprocess.run([exe,'unpack','-h',str(image)],cwd=dest,check=True,capture_output=True)
 new=parse((dest/'ramdisk.cpio').read_bytes());binary=(root/f'work/hmos_{mode}_{version}').read_bytes();assert new['init'][1]==binary;assert new['init.android.original'][1]==old['init'][1];assert new['init.android.original'][0][:11]==old['init'][0][:11]
 for k,v in old.items():
  if k not in ['init','TRAILER!!!']:assert new[k]==v,k
 assert image.stat().st_size==8388608
 assert new['graphics/libdisplay_buffer_vdi_impl.z.so'][1]==(root/'compat/sheng-graphics/padding-v1/libdisplay_buffer_vdi_impl.z.so').read_bytes()
 assert new['hmos-init-debug.cfg'][1]==(root/'tools/configs/init-core-v92.cfg').read_bytes()
 assert new['hmos-ipc.ko'][1]==(root/'compat/sheng-hmos-ipc/v16/sheng_hmos_ipc.ko').read_bytes()
 assert 'token_contract' not in new and 'binder_nested' not in new
 assert new['graphics/touch-bundle.tar.gz'][1]==(root/'compat/sheng-touch/v1/touch-bundle.tar.gz').read_bytes()
 assert new['graphics/libdisplay_composer_vdi_impl.z.so'][1]==(root/'compat/sheng-graphics/framepacing-v1/libdisplay_composer_vdi_impl.z.so').read_bytes()
 form=next(x for x in json.loads(new['graphics/foundation-app-core.json'][1])['systemability'] if x['name']==403)
 assert form==next(x for x in json.loads((root/'work/hmos_system/system/system/profile/foundation.json').read_bytes())['systemability'] if x['name']==403)
 assert b'\r' not in new['graphics/apply-touch.sh'][1]
 assert b'/lib/modules/qcom-pon.ko' in new['graphics/apply-touch.sh'][1]
 assert new['graphics/libsheng_surface_diagnostic.so'][1]==(root/'compat/sheng-graphics/surface-post-v2/libsheng_surface_diagnostic.so').read_bytes()
 assert b'apply-touch.sh' in binary and b'native_input_dispatch' in binary
 assert new['busybox'][1]==(root/'compat/debug-tools/busybox-aarch64').read_bytes()
 assert new['drm-probe'][1]==(root/'compat/debug-tools/drm-probe-aarch64').read_bytes()
 assert 'hmos-native-hilog' in new
 assert new['hmos-hdf-graphics.hcb'][1]==(root/'compat/sheng-graphics/v92/hdf_default.hcb').read_bytes()
 assert new['stock-gpu-firmware/a740_zap.mbn'][1]==(root/'work/stock_odm_runtime/odm/firmware/a740_zap.mbn').read_bytes()
 for file in (root/'compat/sheng-graphics/v92').iterdir():
  if file.is_file():assert new['graphics/'+file.name][1]==file.read_bytes()
 assert gzip.decompress(new['graphics/libvulkan_freedreno.so.gz'][1])==(root/'compat/sheng-graphics/blob-import-v1/libvulkan_freedreno.so').read_bytes()
 assert image.read_bytes()[4096:4100]==bytes.fromhex('02214c18'),'Keep stock vendor legacy-LZ4 stream framing'
 for file in (root/'work/stock_vendor_runtime/vendor/firmware').iterdir():
  if file.name.startswith('a740_') or file.name=='gmu_gen70200.bin':assert new['stock-gpu-firmware/'+file.name][1]==file.read_bytes()
 hardware=json.loads(new['graphics/init-hardware-v92.cfg'][1]);assert {x['name'] for x in hardware['services']}=={'powermgr','media_service','av_session'};assert all(x['once']==1 and 'critical' not in x for x in hardware['services'])
 assert [x['name'] for x in json.loads(new['graphics/powermgr.json'][1])['systemability']]==[3308]
 config=json.loads(new['hmos-init-debug.cfg'][1]);assert {s['name'] for s in config['services']}=={'samgr','hilogd','hdf_devmgr','allocator_host','composer_host','param_watcher','concurrent_task_service','render_service','foundation','accesstoken_service','sheng_snapshot','bootanimation','installs','accountmgr','appspawn','huks_service'} and all(s['once']==1 and 'critical' not in s for s in config['services'])
 assert next(s for s in config['services'] if s['name']=='render_service')['path']==['/compat/bin/native_render_launcher']
 assert next(s for s in config['services'] if s['name']=='accountmgr')['env']==[{'name':'LD_PRELOAD','value':'/compat/lib64/libsheng_account_hmac.so'}]
 assert b'init-persistent-ext4.sh' in binary
 assert 'graphics/libsheng_ram_no_tee.so' in new
 assert 'graphics/libsheng_el5_unavailable.so' in new
 assert len(new['hmos-init-debug.cfg'][1])<32768
 assert 'env' not in next(s for s in config['services'] if s['name']=='appspawn')
 assert 'graphics/libsheng_scb_optional_sa.so' not in new
 assert hashlib.sha256(new['graphics/libnet_tether_manager_if.z.so'][1]).hexdigest()=='6405b690bfe45d1f1567685f05ba0f7db8c54a54b3452dd8ae76b76403200b34'
 assert hashlib.sha256(new['graphics/libsensor_client.z.so'][1]).hexdigest()=='10831009fabed206ab5badca696cb5d0fa61e94aafb2f03a9c13c40cf6781af8'
 assert hashlib.sha256(new['graphics/libsps_privacy_indicator_service_intf.z.so'][1]).hexdigest()=='b193f5ab4919893a90d28ada02c000fccefeb16548f81315175f69802d5af9de'
 assert config['import']==['/compat/etc/init-desktop-services.cfg','/compat/etc/init-hardware-v92.cfg']
 extra=json.loads(new['graphics/init-desktop-services.cfg'][1]);assert {s['name'] for s in extra['services']}=={'storage_daemon','storage_manager','distributeddata','theme_manager_service','wallpaper_service','ui_service','locationhub','multimodalinput','sheng_swipe_probe','sheng_display_wake','useriam','sheng_userauth_host','sheng_input_dispatch','compatibility_config_center','sheng_touch_bridge','sheng_screen_unlock'}
 assert all(s['disabled']==1 and s['once']==1 and 'critical' not in s for s in extra['services'])
 assert next(s for s in extra['services'] if s['name']=='storage_daemon')['path']==['/compat/bin/storage-ram-launcher']
 for asset in ['apply-account-hmac.sh','apply-framework-dev.sh']:
  assert b'\r' not in new['graphics/'+asset][1],asset
 assert new['graphics/sheng_thp_bridge'][1]==(root/'compat/sheng-touch/service-v2/sheng_thp_bridge').read_bytes()
 assert new['graphics/native_input_dispatch'][1]==(root/'compat/debug-tools/native_debug_dispatch_v2').read_bytes()
 assert new['graphics/native_thp_launcher'][1]==(root/'compat/debug-tools/native_thp_launcher').read_bytes()
 assert new['graphics/native_screenlock_request'][1]==(root/'compat/debug-tools/native_screenlock_request_v5').read_bytes()
 assert 'graphics/sheng_gpu_policy' not in new
 assert b'sheng_gpu_policy' not in new['graphics/init-desktop-services.cfg'][1]
 assert b'sheng.debug.start.gpu-policy' not in new['graphics/start-graphics-v92.sh'][1]
 assert b'apply-render-usage.sh' in binary and b'apply-runtime-v92.sh' in binary
 assert b'seek=9162080' in new['graphics/apply-render-usage.sh'][1]
 assert b'sheng-gpu-owner-cleanup' in new['graphics/apply-runtime-v92.sh'][1]
 assert json.loads(new['graphics/oobe_page_offline.json'][1])==[dict(key=x,action='delete') for x in ['wlan','activation_lock','account_login']]
 assert b'AUTOSTART_SERVICES_READY=1' in new['graphics/start-native-desktop-v92.sh'][1]
 assert b'AUTOSTART bootstrap child=' in binary
 assert binary[:4]==b'\x7fELF' and struct.unpack_from('<H',binary,18)[0]==183
 results[mode]={'bytes':image.stat().st_size,'sha256':hashlib.sha256(image.read_bytes()).hexdigest(),'cpio_verified':True,'original_init_preserved':True}
(root/f'analysis/{version}-image-verification.json').write_text(json.dumps(results,indent=2));print(json.dumps(results,indent=2))




















