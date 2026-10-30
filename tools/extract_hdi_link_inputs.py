"""Extract real donor ELF files, resolving its namespace aliases by index.

The Windows EROFS extractor represents links as Cygwin link files. These are
never supplied to the linker as if they were ELF libraries.
"""
from pathlib import Path
import hashlib,json,re,subprocess,shutil,sys
root=Path(__file__).resolve().parent.parent
exe='C:/MIO-KITCHEN-PYSIDE6-5.0.0-PREVIEW/bin/Windows/AMD64/extract.erofs.exe'
image='C:/MIO-KITCHEN-PYSIDE6-5.0.0-PREVIEW/hmos/system.img'
listing=subprocess.check_output([exe,'-i',image,'-P','/system/lib64','-s']).decode('utf-8',errors='replace')
paths=[]
for line in listing.splitlines():
    match=re.search(r'type=FILE .*fsConfig=\[(/system/lib64/[^ ]+)',line)
    if match:paths.append(match[1])
names=[f'libdisplay_composer_proxy_1.{i}.z.so' for i in range(4)]
names += ['libutils.z.so','libhdi_base.z.so','libhdi.z.so','libipc_single.z.so','libipc_common.z.so','libhdf_utils.z.so','libhdifd_parcelable.z.so','libhilog.so','libsec_shared.z.so','libc++.so']
names += sys.argv[1:]
out=root/'work/donor-hdi-link';out.mkdir(exist_ok=True);report=[]
for name in names:
    candidates=[p for p in paths if Path(p).name==name and '/module/' not in p]
    assert len(candidates)==1,(name,candidates)
    path=candidates[0]
    subprocess.run([exe,'-i',image,'-X',path,'-o',str(root/'work/hmos_system'),'-s'],check=True,capture_output=True)
    source=root/'work/hmos_system/system'/path.lstrip('/')
    binary=source.read_bytes();assert binary[:6]==b'\x7fELF\x02\x01',(path,binary[:16])
    shutil.copyfile(source,out/name)
    report.append({'name':name,'original_path':path,'bytes':len(binary),'sha256':hashlib.sha256(binary).hexdigest()})
(root/'analysis/hdi-link-inputs.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps(report,indent=2))
