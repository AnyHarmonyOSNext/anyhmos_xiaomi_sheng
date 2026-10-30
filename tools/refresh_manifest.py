"""Refresh the current source inventory without creating archives or uploading."""
from pathlib import Path
import hashlib
import json

ROOT=Path(__file__).resolve().parent.parent
EXCLUDE={'SOURCE-MANIFEST.json','SHA256SUMS'}
SKIP={'.git','work','out','__pycache__'}


def main():
    files=[]
    for p in sorted(ROOT.rglob('*')):
        relative=p.relative_to(ROOT)
        if (not p.is_file() or p.is_symlink() or any(x in SKIP for x in relative.parts)
                or relative.as_posix() in EXCLUDE):continue
        data=p.read_bytes()
        files.append(dict(path=relative.as_posix(),bytes=len(data),sha256=hashlib.sha256(data).hexdigest()))
    value=dict(format_version=1,hash_algorithm='SHA256',files=files,excludes=sorted(EXCLUDE))
    path=ROOT/'SOURCE-MANIFEST.json'
    path.write_text(json.dumps(value,indent=2)+'\n',encoding='utf-8')
    checks=''.join(f"{v['sha256']}  {v['path']}\n" for v in files)
    checks+=hashlib.sha256(path.read_bytes()).hexdigest()+'  SOURCE-MANIFEST.json\n'
    (ROOT/'SHA256SUMS').write_text(checks,encoding='utf-8')
    print(json.dumps(dict(files=len(files)+2,bytes=sum(v['bytes'] for v in files))))


if __name__=='__main__':main()
