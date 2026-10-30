from pathlib import Path
import zipfile,json,hashlib
r=Path(__file__).resolve().parent.parent
items={
 'README.md':'compat/sheng-graphics/PORTABLE_PATCH_README.md',
 'apply_guarded_elf_patch.py':'tools/apply_guarded_elf_patch.py',
 'bootanimation-eof/patch.json':'compat/sheng-graphics/bootanimation-eof-v1/patch.json',
 'bootanimation-eof/README.md':'compat/sheng-graphics/bootanimation-eof-v1/README.md',
 'rosen-handle-flag/patch.json':'compat/sheng-graphics/rosen-ohos-handle-flag-v1/patch.json',
 'vulkan-context-adapter/adapter.cpp':'tools/bootanimation_vulkan_adapter.cpp',
 'vulkan-context-adapter/launcher.c':'tools/bootanimation_native_launcher.c',
 'vulkan-context-adapter/libsheng_boot_vulkan.so':'compat/sheng-graphics/bootanimation-vulkan-adapter-v1/libsheng_boot_vulkan.so',
 'vulkan-context-adapter/bootanimation-launcher':'compat/sheng-graphics/bootanimation-vulkan-adapter-v1/bootanimation-launcher'}
p=r/'output/sheng-next-display-patch-v2.zip'
with zipfile.ZipFile(p,'w',zipfile.ZIP_DEFLATED) as z:
 for dest,source in items.items():z.write(r/source,dest)
report={'path':str(p.relative_to(r)),'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'files':items,'validation':'original native GPU/RS/HDI actual display accepted by user, v44 cold boot and actual 3048x2032 scanout readback; desktop not ready'}
(r/'analysis/portable-display-patch-v2.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps({k:v for k,v in report.items() if k!='files'},ensure_ascii=False))
