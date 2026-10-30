from pathlib import Path
import hashlib,json,shutil
root=Path.cwd();src=root/'output';dest=Path('C:/MIO-KITCHEN-PYSIDE6-5.0.0-PREVIEW/hmos/debug-v3');dest.mkdir(exist_ok=True)
selected=['boot_stock_303.img','vendor_boot_stock_303.img','init_boot_stock_303.img','init_boot_hmos_probe_v3.img','init_boot_hmos_trace_v3.img','Common.ps1','00-Backup-Recovery.ps1','01-Flash-Probe.ps1','02-Collect-Recovery.ps1','03-Restore-BootChain.ps1','Capture-Serial.ps1','使用说明.md','v3-manifest.json']
for name in selected:shutil.copy2(src/name,dest/name)
for name in ['platform-tools','device-backup']:shutil.copytree(src/name,dest/name,dirs_exist_ok=True)
shutil.copytree(root/'analysis/device-probe-v1',dest/'logs/probe-v1',dirs_exist_ok=True)
(dest/'source').mkdir(exist_ok=True);shutil.copy2(root/'tools/hmos_probe.c',dest/'source/hmos_probe.c')
manifest={}
for p in dest.rglob('*'):
 if not p.is_file() or any(x in p.relative_to(dest).parts for x in ['device-backup','logs']) or p.name=='package-manifest.json':continue
 with p.open('rb') as f:h=hashlib.file_digest(f,'sha256').hexdigest()
 manifest[p.relative_to(dest).as_posix()]={'Bytes':p.stat().st_size,'Sha256':h}
(dest/'package-manifest.json').write_text(json.dumps(manifest,indent=2),encoding='utf-8')
# The workspace also retains earlier images for comparison.
for p in src.glob('init_boot_hmos_*.img'):
 with p.open('rb') as f:h=hashlib.file_digest(f,'sha256').hexdigest()
 manifest[p.name]={'Bytes':p.stat().st_size,'Sha256':h}
(src/'package-manifest.json').write_text(json.dumps(manifest,indent=2),encoding='utf-8')
print('Package saved:',dest)
