"""Build isolated mode/backlight support from the verified v82 composer (WSL)."""
from pathlib import Path
import os,runpy,subprocess,re,json,hashlib
r=Path('/mnt/c/SHENG_WORKSPACE')
b=Path('/root/hmos-work/graphics-deps');p=b/'sheng-graphics-port'
sdk=Path('/root/hmos-work/sdk-6.0.0.47/installed/native')
os.environ.update(ANYHARMONYOS_OHOS_SOURCE=str(b/'source'),ANYHARMONYOS_STAGE=str(b/'stage'),ANYHARMONYOS_ROM_SYSTEM_LIBS=str(r/'work/hmos_system/system/system/lib64'),ANYHARMONYOS_SDK=str(sdk))
cfg=runpy.run_path(str(p/'tools/build_adapter.py'))
out=r/'compat/sheng-graphics/hardware-display-v1';out.mkdir(exist_ok=True)
src=(r/'compat/sheng-graphics/panel-capability-v1/composer_vdi.cpp').read_text()
def replace(old,new):
 global src
 assert src.count(old)==1,old[:100]
 src=src.replace(old,new)
replace('drmModeModeInfo mode{};', '''drmModeModeInfo mode{};
std::vector<drmModeModeInfo> displayModes;
uint32_t selectedMode = 0;
std::map<std::pair<uint32_t, std::string>, uint32_t> propertyIds;''')
replace('#include <map>','#include <map>\n#include <string>')
replace('''    auto *props = drmModeObjectGetProperties(drm, id, type);
    if (!props) return FAIL;
    int result = FAIL;''','''    auto key = std::make_pair(id, std::string(name));
    auto known = propertyIds.find(key);
    if (known != propertyIds.end()) return drmModeAtomicAddProperty(request, id, known->second, value);
    auto *props = drmModeObjectGetProperties(drm, id, type);
    if (!props) return FAIL;
    int result = FAIL;''')
replace('if (!strcmp(name, p->name)) result = drmModeAtomicAddProperty(request, id, p->prop_id, value);','''if (!strcmp(name, p->name)) {
            propertyIds[key] = p->prop_id;
            result = drmModeAtomicAddProperty(request, id, p->prop_id, value);
        }''')
replace('drm = -1; connector = crtc = plane = secondPlane = modeBlob = currentFb = 0;','''drm = -1; connector = crtc = plane = secondPlane = modeBlob = currentFb = 0;
    propertyIds.clear(); displayModes.clear(); selectedMode = 0;''')
replace('''            connector = c->connector_id; mmWidth = c->mmWidth; mmHeight = c->mmHeight;''','''            for (int m = 0; m < c->count_modes; ++m) {
                const auto &candidate = c->modes[m];
                if (candidate.hdisplay != mode.hdisplay || candidate.vdisplay != mode.vdisplay || !candidate.vrefresh) continue;
                if (!memcmp(&candidate, &mode, sizeof(mode))) selectedMode = displayModes.size();
                displayModes.push_back(candidate);
            }
            connector = c->connector_id; mmWidth = c->mmWidth; mmHeight = c->mmHeight;''')
replace('''{ DEVICE_LOCK(id); modes = {{mode.hdisplay, mode.vdisplay, mode.vrefresh, 0}}; return OK; }''','''{
    DEVICE_LOCK(id); modes.clear();
    for (uint32_t i=0;i<displayModes.size();++i) { const auto &m=displayModes[i]; modes.push_back({m.hdisplay,m.vdisplay,m.vrefresh,static_cast<int32_t>(i)}); }
    return OK;
}''')
replace('''{ DEVICE_LOCK(id); modes = {{{mode.hdisplay, mode.vdisplay, mode.vrefresh, 0}, 0}}; return OK; }''','''{
    DEVICE_LOCK(id); modes.clear();
    for (uint32_t i=0;i<displayModes.size();++i) { const auto &m=displayModes[i]; modes.push_back({{m.hdisplay,m.vdisplay,m.vrefresh,static_cast<int32_t>(i)},0}); }
    return OK;
}''')
replace('{ DEVICE_LOCK(id); modeId = 0; return OK; }','{ DEVICE_LOCK(id); modeId = selectedMode; return OK; }')
replace('{ DEVICE_LOCK(id); return modeId == 0 ? OK : UNSUPPORTED; }','''{
    DEVICE_LOCK(id);
    if (modeId >= displayModes.size()) return INVALID;
    if (modeId == selectedMode) return OK;
    uint32_t nextBlob=0;
    if (drmModeCreatePropertyBlob(drm,&displayModes[modeId],sizeof(mode),&nextBlob)) return FAIL;
    auto previousMode=mode; uint32_t previousBlob=modeBlob;
    mode=displayModes[modeId]; modeBlob=nextBlob;
    bool active=false; int result=Active(active);
    if (!result && active) result=client.value.fd>=0 ? Submit(true) : FAIL;
    if (!result && active) result=Submit(false);
    if (result) { mode=previousMode; modeBlob=previousBlob; drmModeDestroyPropertyBlob(drm,nextBlob); return FAIL; }
    drmModeDestroyPropertyBlob(drm,previousBlob); selectedMode=modeId;
    { std::lock_guard<std::mutex> state(vsyncMutex); vsyncPeriod=Period(); }
    Ace5Log("hardware mode selected id=%u refresh=%u active=%d",selectedMode,mode.vrefresh,int(active));
    return OK;
}''')
marker='extern "C" int32_t GetDisplayVBlankPeriod'
assert src.count(marker)==1
src=src.replace(marker,'''// Framework display.para defines 0..255; panel sysfs reports its native scale.
int ReadPanelValue(const char *name, uint32_t &value)
{
    char path[160]; snprintf(path,sizeof(path),"/sys/class/backlight/panel0-backlight/%s",name);
    FILE *file=fopen(path,"r"); if(!file)return FAIL;
    unsigned n=0; int result=fscanf(file,"%u",&n); fclose(file);
    if(result!=1)return FAIL; value=n; return OK;
}
extern "C" int32_t GetDisplayBacklight(uint32_t id, uint32_t &level)
{
    DEVICE_LOCK(id); uint32_t maximum=0,native=0;
    if(ReadPanelValue("max_brightness",maximum)||!maximum||ReadPanelValue("brightness",native)||native>maximum)return FAIL;
    level=(uint64_t(native)*255+maximum/2)/maximum; return OK;
}
extern "C" int32_t SetDisplayBacklight(uint32_t id, uint32_t level)
{
    DEVICE_LOCK(id); if(level>255)return INVALID; uint32_t maximum=0;
    if(ReadPanelValue("max_brightness",maximum)||!maximum)return FAIL;
    uint32_t native=(uint64_t(level)*maximum+127)/255;
    int fd=open("/sys/class/backlight/panel0-backlight/brightness",O_WRONLY|O_CLOEXEC);
    if(fd<0)return FAIL; char text[32]; int length=snprintf(text,sizeof(text),"%u\\n",native);
    ssize_t written; do{written=write(fd,text,length);}while(written<0&&errno==EINTR); int saved=errno;close(fd);errno=saved;
    if(written!=length)return FAIL; uint32_t observed=0;
    if(ReadPanelValue("brightness",observed)||observed!=native)return FAIL;
    Ace5Log("backlight level=%u native=%u max=%u verified=%u",level,native,maximum,observed);return OK;
}
''' + marker)
source=out/'composer_vdi.cpp';source.write_text(src)
# Regenerate unsupported methods locally, without changing reference build files.
implemented=set(re.findall(r'extern "C" int32_t (\w+)\(',src))
implemented.update(re.findall(r'SETTER\((\w+),',src))
header=(p/'generated/vdi-only/composer_exports.h').read_text()
stubs='#include "composer_exports.h"\nnamespace OHOS::HDI::Display::Composer {\n'
for name,args in re.findall(r'extern "C" int32_t (\w+)\((.*?)\);',header,re.S):
 if name not in implemented:stubs+=f'extern "C" int32_t {name}({args}) {{ return -5; }}\n'
stub=out/'composer_unsupported.cpp';stub.write_text(stubs+'}\n')
lib=out/'libdisplay_composer_vdi_impl.z.so'
subprocess.run(cfg['COMMON']+['-I'+str(p/'adapter'),'-shared','-fPIC','-Wl,-z,defs','-Wl,-soname,'+lib.name,str(source),str(stub),str(b/'stage/lib/libdrm.a'),str(cfg['CPP']),'-o',str(lib)],check=True)
subprocess.run([str(sdk/'llvm/bin/llvm-strip'),str(lib)],check=True)
(out/'manifest.json').write_text(json.dumps({f.name:{'bytes':f.stat().st_size,'sha256':hashlib.sha256(f.read_bytes()).hexdigest()} for f in [source,stub,lib]},indent=2)+'\n')
print((out/'manifest.json').read_text())
