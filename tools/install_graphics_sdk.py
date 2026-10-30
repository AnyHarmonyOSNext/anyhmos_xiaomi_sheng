"""Verify official SDK archive and install only its Linux native component."""
from pathlib import Path
import hashlib
import json
import shutil
import subprocess
import tarfile
import zipfile

root=Path('/root/hmos-work/sdk-6.0.0.47')
archive=root/'sdk.tar.gz.part'
expected=(root/'official.sha256').read_text().split()[0].lower()
hasher=hashlib.sha256()
with archive.open('rb') as f:
    for block in iter(lambda:f.read(4*1024*1024),b''):
        hasher.update(block)
digest=hasher.hexdigest()
assert digest==expected, (digest,expected)
print('Official SDK SHA256 verified:',digest,flush=True)
native_zip=root/'native-linux.zip'
with tarfile.open(archive,'r|gz') as tar:
    for member in tar:
        print(member.name,flush=True)
        if member.isfile() and 'native-linux-x64-' in member.name and member.name.endswith('.zip'):
            with tar.extractfile(member) as source,native_zip.open('wb') as output:
                shutil.copyfileobj(source,output)
            break
    else:
        raise RuntimeError('Linux native component not found')
installation=root/'installed'
installation.mkdir(exist_ok=True)
with zipfile.ZipFile(native_zip) as z:
    for name in z.namelist():
        resolved=(installation/name).resolve()
        assert resolved.is_relative_to(installation.resolve()),name
subprocess.run(['unzip','-q','-o',str(native_zip),'-d',str(installation)],check=True)
clang=list(installation.glob('**/llvm/bin/clang'))
assert len(clang)==1,clang
sdk=clang[0].parents[2]
result={'official_archive_sha256':digest,'sdk':str(sdk),'compiler_version':subprocess.check_output([str(clang[0]),'--version'],text=True)}
(root/'installation.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps(result,indent=2))
