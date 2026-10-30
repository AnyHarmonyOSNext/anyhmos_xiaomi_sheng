"""Verify current source inventory, parsers and direct local build inputs."""
from pathlib import Path
import ast
import hashlib
import importlib.util
import json
import re
import subprocess
from urllib.parse import unquote

ROOT=Path(__file__).resolve().parent.parent
manifest=json.loads((ROOT/'SOURCE-MANIFEST.json').read_text())
expected={v['path'] for v in manifest['files']}|{'SOURCE-MANIFEST.json','SHA256SUMS'}
actual={p.relative_to(ROOT).as_posix() for p in ROOT.rglob('*') if p.is_file()
        and not any(x in {'.git','work','out','__pycache__'} for x in p.relative_to(ROOT).parts)}
assert actual==expected,dict(missing=sorted(expected-actual),extra=sorted(actual-expected))
for v in manifest['files']:
    data=(ROOT/v['path']).read_bytes()
    assert len(data)==v['bytes'] and hashlib.sha256(data).hexdigest()==v['sha256'],v['path']
counts=dict(json=0,python=0,shell=0)
for name in sorted(actual):
    p=ROOT/name
    data=p.read_bytes()
    assert b'\0' not in data and not data.startswith((b'\x7fELF',b'MZ')),name
    text=data.decode('utf-8-sig')
    if p.suffix=='.py':ast.parse(text,filename=name);counts['python']+=1
    if p.suffix=='.json':json.loads(text);counts['json']+=1
    if p.suffix=='.sh':
        subprocess.run(['bash','-n',str(p)],check=True);counts['shell']+=1
    if p.suffix=='.md':
        for target in re.findall(r'(?<!!)\[[^\]]+\]\(([^)]+)\)',text):
            if '://' in target or target.startswith('#'):continue
            assert (p.parent/unquote(target.split('#')[0].strip('<>'))).exists(),(name,target)
    if p.suffix in {'.cpp','.c','.h','.hpp','.inc'}:
        for target in re.findall(r'^\s*#\s*include\s*"([^"\n]+\.(?:cpp|inc))"',text,re.M):
            assert (p.parent/target).is_file(),(name,target)
spec=importlib.util.spec_from_file_location('build_current',ROOT/'tools/build_current.py')
module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
plan=module.commands(ROOT/'work/current-build')
source_count=0
for name,command in plan.items():
    for value in command:
        if value.endswith(('.c','.cpp','.S')) and value.startswith(str(ROOT)):
            assert Path(value).is_file(),(name,value);source_count+=1
print(json.dumps(dict(files=len(actual),manifest_verified=True,parsers=counts,
    direct_build_targets=len(plan),build_source_inputs=source_count,local_links_verified=True),indent=2))
