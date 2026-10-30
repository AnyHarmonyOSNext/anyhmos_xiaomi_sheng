"""Extend the tested shared tail to standard color/HDR/crop metadata keys."""
from pathlib import Path
import os, runpy, subprocess, hashlib, json
r = Path(__file__).resolve().parent.parent
b = Path('/root/hmos-work/graphics-deps'); port = b/'sheng-graphics-port'
sdk = Path('/root/hmos-work/sdk-6.0.0.47/installed/native')
os.environ.update(ANYHARMONYOS_OHOS_SOURCE=str(b/'source'),ANYHARMONYOS_STAGE=str(b/'stage'),ANYHARMONYOS_ROM_SYSTEM_LIBS=str(r/'work/hmos_system/system/system/lib64'),ANYHARMONYOS_SDK=str(sdk))
cfg = runpy.run_path(str(port/'tools/build_adapter.py'))
out = r/'compat/sheng-graphics/metadata-v124'; out.mkdir(exist_ok=True)
s = (r/'compat/sheng-graphics/crop-v123/buffer_vdi.cpp').read_text()
def replace(old,new):
    global s
    assert s.count(old)==1,old[:100]
    s=s.replace(old,new)
replace('CROP_VERSION = 1;', 'CROP_VERSION = 2;')
replace('struct CropStore { uint32_t magic, version, locked, present, rect[4]; };', '''struct CropStore {
    uint32_t magic, version, locked, present, lengths[9];
    uint8_t values[8][256], dynamicHdr[1024];
    uint8_t *Value(uint32_t key) { return key == 5 ? dynamicHdr : values[key > 5 ? key - 2 : key - 1]; }
};
static_assert(sizeof(CropStore) <= 4096);
bool KnownMetadata(uint32_t key) { return key >= 1 && key <= 9; }
bool ValidMetadata(uint32_t key, size_t size) {
    switch (key) {
        case 1: case 7: return size == 16;
        case 2: case 3: case 6: case 8: case 9: return size == 4;
        case 4: return size > 0 && size <= 256;
        case 5: return size > 0 && size <= 1024;
        default: return false;
    }
}''')
start=s.index('    int32_t SetMetadata('); end=s.index('    int32_t GetImageLayout(',start)
s=s[:start]+'''    int32_t SetMetadata(const BufferHandle &h, uint32_t key, const std::vector<uint8_t> &value) override
    {
        if (!KnownMetadata(key)) return UNSUPPORTED;
        if (!ValidMetadata(key, value.size())) return INVALID;
        if (key == CROP_KEY) {
            uint32_t rect[4]; memcpy(rect, value.data(), sizeof(rect));
            if (!rect[2] || !rect[3] || uint64_t(rect[0]) + rect[2] > uint32_t(h.width) ||
                uint64_t(rect[1]) + rect[3] > uint32_t(h.height)) return INVALID;
        }
        CropMapping m(h);
        if (!m.locked) return UNSUPPORTED;
        memcpy(m.store->Value(key), value.data(), value.size());
        m.store->lengths[key - 1] = value.size(); m.store->present |= 1u << (key - 1);
        return OK;
    }
    int32_t GetMetadata(const BufferHandle &h, uint32_t key, std::vector<uint8_t> &value) override
    {
        if (!KnownMetadata(key)) return UNSUPPORTED;
        CropMapping m(h);
        if (!m.locked || !(m.store->present & (1u << (key - 1)))) return UNSUPPORTED;
        const size_t length = m.store->lengths[key - 1];
        if (!ValidMetadata(key, length)) return INVALID;
        const auto *p = m.store->Value(key); value.assign(p, p + length); return OK;
    }
    int32_t ListMetadataKeys(const BufferHandle &h, std::vector<uint32_t> &keys) override
    {
        CropMapping m(h);
        if (!m.locked) return UNSUPPORTED;
        keys.clear();
        for (uint32_t key = 1; key <= 9; ++key)
            if (m.store->present & (1u << (key - 1))) keys.push_back(key);
        return OK;
    }
    int32_t EraseMetadataKey(const BufferHandle &h, uint32_t key) override
    {
        if (!KnownMetadata(key)) return UNSUPPORTED;
        CropMapping m(h);
        if (!m.locked) return UNSUPPORTED;
        m.store->present &= ~(1u << (key - 1)); m.store->lengths[key - 1] = 0;
        memset(m.store->Value(key), 0, key == 5 ? 1024 : 256); return OK;
    }
'''+s[end:]
(out/'buffer_vdi.cpp').write_text(s)
t=(r/'tools/crop_metadata_probe_v123.cpp').read_text()
t=t.replace('    const pid_t pid = fork();', '''    std::vector<uint8_t> color(16, 0); color[0] = 1; color[4] = 1; color[8] = 1;
    CHECK(vdi->SetMetadata(*h, 1, color) == 0);
    const pid_t pid = fork();''')
t=t.replace('        uint32_t update[4]', '''        if (vdi->GetMetadata(imported, 1, got) || got != color) _exit(4);
        uint32_t update[4]''')
t=t.replace('keys == std::vector<uint32_t>{7}', 'keys.size() == 2 && keys[0] == 1 && keys[1] == 7')
t=t.replace('SetMetadata(*h, 1, value) != 0', 'SetMetadata(*h, 31, value) != 0')
t=t.replace('    CHECK(vdi->ListMetadataKeys(*h, keys) == 0 && keys.empty());', '    CHECK(vdi->EraseMetadataKey(*h, 1) == 0);\n    CHECK(vdi->ListMetadataKeys(*h, keys) == 0 && keys.empty());')
t=t.replace('CROP_METADATA_PASS','BUFFER_METADATA_PASS')
(out/'metadata_probe.cpp').write_text(t)
report={}
for name,args in [
    ('libdisplay_buffer_vdi_impl.z.so', ['-DACE5_LINEAR_STRIDE_ALIGNMENT=128','-shared','-fPIC','-Wl,-z,defs','-Wl,-soname,libdisplay_buffer_vdi_impl.z.so',str(out/'buffer_vdi.cpp')]),
    ('metadata_probe', [str(out/'metadata_probe.cpp')])]:
    target=out/name
    subprocess.run(cfg['COMMON']+['-I'+str(port/'adapter')]+args+[str(cfg['CPP']),'-o',str(target)],check=True)
    subprocess.run([str(sdk/'llvm/bin/llvm-strip'),str(target)],check=True)
    report[name]=dict(bytes=target.stat().st_size,sha256=hashlib.sha256(target.read_bytes()).hexdigest())
(out/'manifest.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps(report))
