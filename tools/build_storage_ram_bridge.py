from pathlib import Path
import subprocess,json,hashlib
r=Path('/mnt/c/SHENG_WORKSPACE');d=r/'compat/sheng-framework/account-hmac-v1'
sdk=Path('/root/hmos-work/sdk-6.0.0.47/installed/native/llvm/bin')
for source,out,extra in [('storage_ram_no_tee.c','libsheng_ram_no_tee.so',['-shared','-fPIC','-Wl,-z,relro,-z,now']),('storage_ram_launcher.c','storage-ram-launcher',[])]:
    subprocess.run([str(sdk/'clang'),'--target=aarch64-linux-ohos','-O2','-Wall','-Wextra','-Werror',str(d/source),*extra,'-o',str(d/out)],check=True)
    subprocess.run([str(sdk/'llvm-strip'),str(d/out)],check=True)
report={name:{'bytes':(d/name).stat().st_size,'sha256':hashlib.sha256((d/name).read_bytes()).hexdigest()} for name in ['libsheng_ram_no_tee.so','storage-ram-launcher']}
report['original_storage_daemon_sha256']=hashlib.sha256((r/'work/hmos_system/system/system/bin/storage_daemon').read_bytes()).hexdigest()
report['scope']='RAM-only, original fscrypt-disabled path; unavailable HDI is NULL, optional auth upgrade remains unsupported; no fake secure operation success'
(d/'storage-ram-manifest.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))
