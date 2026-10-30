"""Recover diagnostic symbol offsets only if the rebuilt production hash matches."""
from pathlib import Path
import hashlib, json, os, runpy, shutil, struct, subprocess

r = Path(__file__).resolve().parent.parent
b = Path('/root/hmos-work/graphics-deps')
port = b / 'sheng-graphics-port'
sdk = Path('/root/hmos-work/sdk-6.0.0.47/installed/native')
os.environ.update(ANYHARMONYOS_OHOS_SOURCE=str(b/'source'), ANYHARMONYOS_STAGE=str(b/'stage'),
    ANYHARMONYOS_ROM_SYSTEM_LIBS=str(r/'work/hmos_system/system/system/lib64'), ANYHARMONYOS_SDK=str(sdk))
cfg = runpy.run_path(str(port/'tools/build_adapter.py'))
d = r/'work/vdi-uprobe-v129'; d.mkdir(exist_ok=True)
debug = d/'libdisplay_buffer_vdi_impl.debug.so'
subprocess.run(cfg['COMMON']+['-I'+str(port/'adapter'), '-DACE5_LINEAR_STRIDE_ALIGNMENT=128',
    '-shared', '-fPIC', '-Wl,-z,defs', '-Wl,-soname,libdisplay_buffer_vdi_impl.z.so',
    str(r/'compat/sheng-graphics/rgb-metadata-v129/buffer_vdi.cpp'), str(cfg['CPP']), '-o', str(debug)], check=True)
stripped = d/'stripped.so'; shutil.copyfile(debug, stripped)
subprocess.run([str(sdk/'llvm/bin/llvm-strip'), str(stripped)], check=True)
h = hashlib.sha256(stripped.read_bytes()).hexdigest()
assert h == '185e8d8e400f14d467c1f742f542225b1ad03dedb603f47f189f32edf6a28e24', h
raw = debug.read_bytes(); phoff = struct.unpack_from('<Q',raw,32)[0]
phsize,phnum = struct.unpack_from('<HH',raw,54)
segments = [struct.unpack_from('<IIQQQQQQ',raw,phoff+i*phsize) for i in range(phnum)]
symbols = subprocess.check_output([str(sdk/'llvm/bin/llvm-nm'), '-n', '-C', '--defined-only', str(debug)], text=True)
result = {'production_sha256':h, 'symbols':{}}
for line in symbols.splitlines():
    if 'LinearBuffer::SetMetadata(' not in line and 'LinearBuffer::GetMetadata(' not in line: continue
    addr,kind,name=line.split(maxsplit=2); addr=int(addr,16)
    segment = next(p for p in segments if p[0]==1 and p[3]<=addr<p[3]+p[5])
    result['symbols'][name]={'address':addr,'file_offset':addr-segment[3]+segment[2]}
assert len(result['symbols'])==2
(r/'analysis/vdi-uprobe-map-v129.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps(result,indent=2))
