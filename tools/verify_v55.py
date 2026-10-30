from pathlib import Path
import subprocess,struct,json,sys,hashlib,gzip
version='v55';root=Path.cwd();exe='C:/MIO-KITCHEN-PYSIDE6-5.0.0-PREVIEW/bin/Windows/AMD64/magiskboot.exe'
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
 assert new['hmos-init-debug.cfg'][1]==(root/'tools/configs/init-core-v55.cfg').read_bytes()
 assert new['hmos-ipc.ko'][1]==(root/'compat/sheng-hmos-ipc/v16/sheng_hmos_ipc.ko').read_bytes()
 for test in ['token_contract','binder_nested']:assert new[test][1]==(root/'compat/sheng-hmos-ipc/tests'/test).read_bytes()
 assert new['busybox'][1]==(root/'compat/debug-tools/busybox-aarch64').read_bytes()
 assert new['drm-probe'][1]==(root/'compat/debug-tools/drm-probe-aarch64').read_bytes()
 assert 'hmos-native-hilog' in new
 assert new['hmos-hdf-graphics.hcb'][1]==(root/'compat/sheng-graphics/v55/hdf_default.hcb').read_bytes()
 assert new['stock-gpu-firmware/a740_zap.mbn'][1]==(root/'work/stock_odm_runtime/odm/firmware/a740_zap.mbn').read_bytes()
 for file in (root/'compat/sheng-graphics/v55').iterdir():
  if file.is_file():assert new['graphics/'+file.name][1]==file.read_bytes()
 assert gzip.decompress(new['graphics/libvulkan_freedreno.so.gz'][1])==(root/'compat/sheng-graphics/gpu-v1/libvulkan_freedreno.so').read_bytes()
 assert image.read_bytes()[4096:4100]==bytes.fromhex('02214c18'),'Keep stock vendor legacy-LZ4 stream framing'
 for file in (root/'work/stock_vendor_runtime/vendor/firmware').iterdir():
  if file.name.startswith('a740_') or file.name=='gmu_gen70200.bin':assert new['stock-gpu-firmware/'+file.name][1]==file.read_bytes()
 config=json.loads(new['hmos-init-debug.cfg'][1]);assert {s['name'] for s in config['services']}=={'samgr','hilogd','hdf_devmgr','allocator_host','composer_host','param_watcher','concurrent_task_service','render_service','foundation','accesstoken_service','sheng_snapshot','bootanimation','installs','accountmgr','appspawn','huks_service'} and all(s['once']==1 and 'critical' not in s for s in config['services'])
 assert next(s for s in config['services'] if s['name']=='accountmgr')['env']==[{'name':'LD_PRELOAD','value':'/compat/lib64/libsheng_account_hmac.so'}]
 assert b'init-persistent-ext4.sh' in binary
 assert 'graphics/libsheng_ram_no_tee.so' in new
 assert len(new['hmos-init-debug.cfg'][1])<32768
 assert config['import']==['/compat/etc/init-desktop-services.cfg']
 extra=json.loads(new['graphics/init-desktop-services.cfg'][1]);assert {s['name'] for s in extra['services']}=={'storage_daemon','storage_manager','distributeddata'}
 assert all(s['disabled']==1 and s['once']==1 and 'critical' not in s for s in extra['services'])
 assert next(s for s in extra['services'] if s['name']=='storage_daemon')['path']==['/compat/bin/storage-ram-launcher']
 for asset in ['apply-account-hmac.sh','apply-framework-dev.sh']:
  assert b'\r' not in new['graphics/'+asset][1],asset
 assert binary[:4]==b'\x7fELF' and struct.unpack_from('<H',binary,18)[0]==183
 results[mode]={'bytes':image.stat().st_size,'sha256':hashlib.sha256(image.read_bytes()).hexdigest(),'cpio_verified':True,'original_init_preserved':True}
(root/f'analysis/{version}-image-verification.json').write_text(json.dumps(results,indent=2));print(json.dumps(results,indent=2))




















