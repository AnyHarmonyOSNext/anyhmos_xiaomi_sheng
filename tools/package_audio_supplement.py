"""Read-only original303 plugins/config/amp-firmware supplement for /compat."""
from pathlib import Path
import hashlib
import json
import shutil
import subprocess
import tarfile

r = Path(__file__).resolve().parent.parent
base = Path('C:/MIO-KITCHEN-PYSIDE6-5.0.0-PREVIEW/303')
extracted = r/'work/stock-audio-supplement'
root = r/'work/audio-supplement-v1'
exe = 'C:/MIO-KITCHEN-PYSIDE6-5.0.0-PREVIEW/bin/Windows/AMD64/extract.erofs.exe'
manifest = {}

def add(src, path):
    dst = root/path
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(src, dst)
    manifest[path] = dict(source=str(src.relative_to(r)), bytes=src.stat().st_size,
                          sha256=hashlib.sha256(src.read_bytes()).hexdigest())

for name in ['libagm_mixer_plugin.so', 'libagm_pcm_plugin.so', 'libagm_compress_plugin.so', 'libsndcardparser.so']:
    path = '/lib64/'+name
    subprocess.run([exe, '-i', str(base/'vendor.img'), '-X', path, '-o', str(extracted), '-s'], capture_output=True, check=True)
    add(extracted/'vendor'/path.lstrip('/'), 'lib64/'+name)
add(r/'work/stock-audio-runtime/vndk33/libbacktrace.so', 'lib64/libbacktrace.so')
for part, paths in {
    'vendor': ['/etc/card-defs.xml', '/etc/kvh2xml.xml', '/etc/usecaseKvManager.xml'],
    'odm': ['/etc/usecaseKvManager.xml'],
}.items():
    for path in paths:
        subprocess.run([exe, '-i', str(base/(part+'.img')), '-X', path, '-o', str(extracted), '-s'], capture_output=True, check=True)
        add(extracted/part/path.lstrip('/'), 'config/'+part+path)
for p in (r/'work/stock-audio-reference/odm/etc/audio/sku_kalama').glob('*.xml'):
    add(p, 'config/odm/etc/audio/sku_kalama/'+p.name)
add(r/'work/stock-audio-runtime/odm/etc/audio/sku_kalama/resourcemanager_kalama_mtp.xml',
    'config/odm/etc/audio/sku_kalama/resourcemanager_kalama_mtp.xml')
for p in (r/'work/stock-audio-runtime/odm/firmware').iterdir():
    add(p, 'firmware/'+p.name)
(root/'manifest.json').write_text(json.dumps(manifest, indent=2)+'\n')
archive = r/'output/audio-supplement-v1.tar.gz'
with tarfile.open(archive, 'w:gz') as tar:
    for p in sorted(root.rglob('*')):
        if p.is_file():
            info = tar.gettarinfo(str(p), str(p.relative_to(root)))
            info.mode = 0o644
            info.uid = info.gid = 0
            info.uname = info.gname = ''
            with p.open('rb') as f:
                tar.addfile(info, f)
b = archive.read_bytes()
assert len(b) <= 1048576
info = dict(path=str(archive.relative_to(r)), bytes=len(b), sha256=hashlib.sha256(b).hexdigest())
(r/'analysis/audio-supplement-v1-package.json').write_text(json.dumps(info, indent=2)+'\n')
print(json.dumps(info, indent=2))
