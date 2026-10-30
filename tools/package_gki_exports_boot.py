from pathlib import Path
import hashlib,json,shutil,struct,subprocess
root=Path(__file__).resolve().parent.parent
verification=json.loads((root/'analysis/gki-sheng-exports-verification.json').read_text())
assert verification['cfi_enabled'] and not verification['changed'] and not verification['removed']
gki=Path('/root/hmos-work/gki-out-sheng-exports/arch/arm64/boot/Image')
image=root/'output/kernel_sheng_exports_303.Image'
subprocess.run(['wsl','-d','Ubuntu-22.04','--','cp',gki.as_posix(),'/mnt/c/SHENG_WORKSPACE/output/kernel_sheng_exports_303.Image'],check=True)
stock=Path('E:/SHENG_STOCK_303/images/boot.img')
tool='C:/MIO-KITCHEN-PYSIDE6-5.0.0-PREVIEW/bin/Windows/AMD64/magiskboot.exe'
folder=root/'work/boot_sheng_exports';folder.mkdir(exist_ok=True)
shutil.copy2(root/'work/stock_boot/header',folder/'header');shutil.copy2(image,folder/'kernel')
boot=root/'output/boot_sheng_exports_303.img'
subprocess.run([tool,'repack',str(stock),str(boot)],cwd=folder,check=True)
check=root/'work/verify_boot_sheng_exports';check.mkdir(exist_ok=True)
subprocess.run([tool,'unpack','-h',str(boot)],cwd=check,check=True,capture_output=True)
assert (check/'kernel').read_bytes()==image.read_bytes()
a,b=stock.read_bytes(),boot.read_bytes()
assert b[:8]==b'ANDROID!' and struct.unpack_from('<I',b,40)[0]==4
assert struct.unpack_from('<I',b,12)[0]==0 and a[16:1580]==b[16:1580]
assert len(b)==len(a)==100663296
manifest={'compatibility':{'abi_verified':True,'cfi_enabled':True,'old_exports_unchanged':verification['unchanged_old_exports']}}
for p in [boot,image]:
 with p.open('rb') as stream:manifest[p.name]={'Bytes':p.stat().st_size,'Sha256':hashlib.file_digest(stream,'sha256').hexdigest()}
(root/'output/kernel-sheng-exports-manifest.json').write_text(json.dumps(manifest,indent=2))
print(json.dumps(manifest,indent=2))
