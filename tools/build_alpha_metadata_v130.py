"""Store the observed standard FORCE_GLOBAL_ALPHA key; reject invalid values."""
from pathlib import Path
import hashlib,json,os,runpy,subprocess
r=Path(__file__).resolve().parent.parent
b=Path('/root/hmos-work/graphics-deps');port=b/'sheng-graphics-port'
sdk=Path('/root/hmos-work/sdk-6.0.0.47/installed/native')
out=r/'compat/sheng-graphics/alpha-metadata-v130';out.mkdir(exist_ok=True)
s=(r/'compat/sheng-graphics/rgb-metadata-v129/buffer_vdi.cpp').read_text()
changes={
 'CROP_VERSION = 2;':'CROP_VERSION = 3;',
 'uint8_t values[8][256], dynamicHdr[1024];':'uint8_t values[8][256], dynamicHdr[1024];\n    uint32_t forceAlphaLength; int32_t forceAlpha;',
 'uint8_t *Value(uint32_t key) { return key == 5 ? dynamicHdr : values[key > 5 ? key - 2 : key - 1]; }':
 'uint8_t *Value(uint32_t key) { return key == 12 ? reinterpret_cast<uint8_t *>(&forceAlpha) : key == 5 ? dynamicHdr : values[key > 5 ? key - 2 : key - 1]; }\n    uint32_t &Length(uint32_t key) { return key == 12 ? forceAlphaLength : lengths[key - 1]; }',
 'return key >= 1 && key <= 9;':'return (key >= 1 && key <= 9) || key == 12;',
 'case 2: case 3: case 6: case 8: case 9: return size == 4;':
 'case 2: case 3: case 6: case 8: case 9: case 12: return size == 4;',
 'if (!ValidMetadata(key, value.size())) return INVALID;':
 '''if (!ValidMetadata(key, value.size())) return INVALID;
        if (key == 12) {
            int32_t alpha; memcpy(&alpha, value.data(), sizeof(alpha));
            if (alpha < -1 || alpha > 255) return INVALID;
        }''',
 'for (uint32_t key = 1; key <= 9; ++key)':
 'for (uint32_t key : {1u,2u,3u,4u,5u,6u,7u,8u,9u,12u})',
 'memset(m.store->Value(key), 0, key == 5 ? 1024 : 256);':
 'memset(m.store->Value(key), 0, key == 12 ? 4 : key == 5 ? 1024 : 256);',
}
for old,new in changes.items():
 assert s.count(old)==1,old
 s=s.replace(old,new)
assert s.count('m.store->lengths[key - 1]')==3
s=s.replace('m.store->lengths[key - 1]','m.store->Length(key)')
(out/'buffer_vdi.cpp').write_text(s)
t=(r/'tools/rgb_metadata_probe_v129.cpp').read_text()
t=t.replace('pid_t child = fork();', '''int32_t alpha = -1; std::vector<uint8_t> alphaBytes(4);
        memcpy(alphaBytes.data(), &alpha, 4); CHECK(!v->SetMetadata(*h, 12, alphaBytes));
        pid_t child = fork();''')
t=t.replace('uint32_t update[4]', '''if (v->GetMetadata(imported, 12, got) || got != alphaBytes) _exit(4);
            alpha = 127; memcpy(alphaBytes.data(), &alpha, 4);
            if (v->SetMetadata(imported, 12, alphaBytes)) _exit(5);
            uint32_t update[4]''')
t=t.replace('CHECK(v->SetMetadata(*h, 1,', '''CHECK(!v->GetMetadata(*h, 12, got) && got.size() == 4);
        memcpy(&alpha, got.data(), 4); CHECK(alpha == 127);
        for (int32_t invalid : {-2, 256}) {
            memcpy(alphaBytes.data(), &invalid, 4); CHECK(v->SetMetadata(*h, 12, alphaBytes) != 0);
        }
        CHECK(v->SetMetadata(*h, 12, std::vector<uint8_t>(8)) != 0);
        CHECK(v->SetMetadata(*h, 10, alphaBytes) != 0);
        CHECK(v->SetMetadata(*h, 11, alphaBytes) != 0);
        CHECK(v->SetMetadata(*h, 1,''')
t=t.replace('std::vector<uint32_t>{1, 7}', 'std::vector<uint32_t>{1, 7, 12}')
t=t.replace('pixels = static_cast<unsigned char *>(v->Mmap(*h)); CHECK(pixels);\n        CHECK(!v->InvalidateCache(*h));\n        for',
 '''CHECK(!v->EraseMetadataKey(*h, 12)); CHECK(v->GetMetadata(*h, 12, got) != 0);
        CHECK(!v->GetMetadata(*h, 7, got) && got.size() == 16 && !memcmp(got.data(), updated, 16));
        pixels = static_cast<unsigned char *>(v->Mmap(*h)); CHECK(pixels);
        CHECK(!v->InvalidateCache(*h));
        for''')
t=t.replace('RGB_METADATA_CONTRACT=0','ALPHA_METADATA_CONTRACT=0').replace('RGB_YUV_METADATA_PASS','ALPHA_METADATA_PASS')
(out/'alpha_metadata_probe.cpp').write_text(t)
os.environ.update(ANYHARMONYOS_OHOS_SOURCE=str(b/'source'),ANYHARMONYOS_STAGE=str(b/'stage'),
 ANYHARMONYOS_ROM_SYSTEM_LIBS=str(r/'work/hmos_system/system/system/lib64'),ANYHARMONYOS_SDK=str(sdk))
cfg=runpy.run_path(str(port/'tools/build_adapter.py'));report={}
for name,args in [
 ('libdisplay_buffer_vdi_impl.z.so',['-DACE5_LINEAR_STRIDE_ALIGNMENT=128','-shared','-fPIC','-Wl,-z,defs','-Wl,-soname,libdisplay_buffer_vdi_impl.z.so',str(out/'buffer_vdi.cpp')]),
 ('alpha_metadata_probe',[str(out/'alpha_metadata_probe.cpp')])]:
 target=out/name
 subprocess.run(cfg['COMMON']+['-I'+str(port/'adapter')]+args+[str(cfg['CPP']),'-o',str(target)],check=True)
 subprocess.run([str(sdk/'llvm/bin/llvm-strip'),str(target)],check=True)
 report[name]=dict(bytes=target.stat().st_size,sha256=hashlib.sha256(target.read_bytes()).hexdigest())
(out/'manifest.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report))
