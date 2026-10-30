"""Add real cross-process crop metadata in a separate YUV DMA-BUF tail page."""
from pathlib import Path
import os, runpy, subprocess, hashlib, json

r = Path(__file__).resolve().parent.parent
b = Path('/root/hmos-work/graphics-deps')
port = b/'sheng-graphics-port'
sdk = Path('/root/hmos-work/sdk-6.0.0.47/installed/native')
os.environ.update(ANYHARMONYOS_OHOS_SOURCE=str(b/'source'), ANYHARMONYOS_STAGE=str(b/'stage'), ANYHARMONYOS_ROM_SYSTEM_LIBS=str(r/'work/hmos_system/system/system/lib64'), ANYHARMONYOS_SDK=str(sdk))
cfg = runpy.run_path(str(port/'tools/build_adapter.py'))
out = r/'compat/sheng-graphics/crop-v123'
out.mkdir(exist_ok=True)
s = (r/'compat/sheng-graphics/padding-v1/buffer_vdi.cpp').read_text()
def replace(old, new):
    global s
    assert s.count(old) == 1, old[:90]
    s = s.replace(old, new)
replace('#include <cstdlib>', '#include <cstdlib>\n#include <cstring>\n#include <sched.h>')
replace('class LinearBuffer final', '''// The pixel allocation retains its original stride and offsets. Only new YUV
// buffers carry one extra, page-aligned CPU metadata page, outside all pixels.
// No extra handle FD/integer fields or GPU/display format changes are needed.
constexpr uint32_t CROP_KEY = 7, CROP_MAGIC = 0x53435250, CROP_VERSION = 1;
struct CropStore { uint32_t magic, version, locked, present, rect[4]; };
class CropMapping {
public:
    CropStore *store = nullptr;
    bool locked = false;
    explicit CropMapping(const BufferHandle &h) {
        uint32_t stride; uint64_t pixels;
        if (!Valid(h) || !IsSemiPlanar420(h.format) ||
            !Layout(h.width, h.height, h.usage, h.format, stride, pixels) ||
            uint64_t(h.size) < ((pixels + 4095) & ~4095ULL) + 4096 || h.size % 4096) return;
        void *p = mmap(nullptr, 4096, PROT_READ | PROT_WRITE, MAP_SHARED, h.fd, h.size - 4096);
        if (p == MAP_FAILED) return;
        store = static_cast<CropStore *>(p);
        if (store->magic != CROP_MAGIC || store->version != CROP_VERSION) return;
        for (int i = 0; i < 32; ++i) {
            uint32_t expected = 0;
            if (__atomic_compare_exchange_n(&store->locked, &expected, 1, false,
                __ATOMIC_ACQUIRE, __ATOMIC_RELAXED)) { locked = true; break; }
            sched_yield();
        }
    }
    ~CropMapping() {
        if (locked) __atomic_store_n(&store->locked, 0, __ATOMIC_RELEASE);
        if (store) munmap(store, 4096);
    }
};
class LinearBuffer final''')
replace('        size = (size + 4095) & ~4095ULL;', '''        size = (size + 4095) & ~4095ULL;
        if (IsSemiPlanar420(info.format)) size += 4096;
        if (size > MAX_SIZE) return INVALID;''')
replace('        handle = h;', '''        if (IsSemiPlanar420(info.format)) {
            void *p = mmap(nullptr, 4096, PROT_READ | PROT_WRITE, MAP_SHARED, h->fd, size - 4096);
            if (p == MAP_FAILED) { close(h->fd); free(h); return FAIL; }
            memset(p, 0, 4096);
            auto *meta = static_cast<CropStore *>(p);
            meta->magic = CROP_MAGIC; meta->version = CROP_VERSION;
            munmap(p, 4096);
        }
        handle = h;''')
start = s.index('    int32_t SetMetadata(')
end = s.index('    int32_t GetImageLayout(', start)
s = s[:start] + '''    int32_t SetMetadata(const BufferHandle &h, uint32_t key, const std::vector<uint8_t> &value) override
    {
        if (key != CROP_KEY) return UNSUPPORTED;
        if (value.size() != sizeof(uint32_t) * 4) return INVALID;
        uint32_t rect[4]; memcpy(rect, value.data(), sizeof(rect));
        if (!rect[2] || !rect[3] || uint64_t(rect[0]) + rect[2] > uint32_t(h.width) ||
            uint64_t(rect[1]) + rect[3] > uint32_t(h.height)) return INVALID;
        CropMapping m(h);
        if (!m.locked) return UNSUPPORTED;
        memcpy(m.store->rect, rect, sizeof(rect)); m.store->present = 1;
        return OK;
    }
    int32_t GetMetadata(const BufferHandle &h, uint32_t key, std::vector<uint8_t> &value) override
    {
        if (key != CROP_KEY) return UNSUPPORTED;
        CropMapping m(h);
        if (!m.locked || !m.store->present) return UNSUPPORTED;
        const auto *p = reinterpret_cast<const uint8_t *>(m.store->rect);
        value.assign(p, p + sizeof(m.store->rect)); return OK;
    }
    int32_t ListMetadataKeys(const BufferHandle &h, std::vector<uint32_t> &keys) override
    {
        CropMapping m(h);
        if (!m.locked) return UNSUPPORTED;
        keys.clear(); if (m.store->present) keys.push_back(CROP_KEY);
        return OK;
    }
    int32_t EraseMetadataKey(const BufferHandle &h, uint32_t key) override
    {
        if (key != CROP_KEY) return UNSUPPORTED;
        CropMapping m(h);
        if (!m.locked) return UNSUPPORTED;
        m.store->present = 0; memset(m.store->rect, 0, sizeof(m.store->rect));
        return OK;
    }
''' + s[end:]
(out/'buffer_vdi.cpp').write_text(s)
commands = [
    ('libdisplay_buffer_vdi_impl.z.so', cfg['COMMON']+['-I'+str(port/'adapter'), '-DACE5_LINEAR_STRIDE_ALIGNMENT=128', '-shared', '-fPIC', '-Wl,-z,defs', '-Wl,-soname,libdisplay_buffer_vdi_impl.z.so', str(out/'buffer_vdi.cpp')]),
    ('crop_metadata_probe', cfg['COMMON']+['-I'+str(port/'adapter'), str(r/'tools/crop_metadata_probe_v123.cpp')])]
report = {}
for name, command in commands:
    target = out/name
    subprocess.run(command+[str(cfg['CPP']), '-o', str(target)], check=True)
    subprocess.run([str(sdk/'llvm/bin/llvm-strip'), str(target)], check=True)
    report[name] = dict(bytes=target.stat().st_size, sha256=hashlib.sha256(target.read_bytes()).hexdigest())
(out/'manifest.json').write_text(json.dumps(report, indent=2)+'\n')
print(json.dumps(report))
