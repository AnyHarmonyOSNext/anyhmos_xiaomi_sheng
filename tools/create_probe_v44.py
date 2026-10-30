"""Package physically accepted native RS boot diagnostic chain for cold boot."""
from pathlib import Path
import shutil,json,hashlib
r=Path(__file__).resolve().parent.parent
for name in ['hmos_probe.c','probe_graphics.inc','probe_command.inc']:
 dest=r/'tools/archive'/(Path(name).stem+'_v43'+Path(name).suffix)
 if not dest.exists():shutil.copy2(r/'tools'/name,dest)
p=r/'tools/hmos_probe.c';p.write_text(p.read_text(encoding='utf-8').replace('v43','v44'),encoding='utf-8')
cfg=json.loads((r/'tools/configs/init-core-v43.cfg').read_text(encoding='utf-8'))
boot=next(s for s in cfg['services'] if s['name']=='bootanimation')
if 'dev_dma_heap' not in boot['gid']:boot['gid'].append('dev_dma_heap')
(r/'tools/configs/init-core-v44.cfg').write_text(json.dumps(cfg,indent=2)+'\n',encoding='utf-8')
dest=r/'compat/sheng-graphics/v44';shutil.copytree(r/'compat/sheng-graphics/v43',dest,dirs_exist_ok=True)
assets={
 'bootanimation-real':'bootanimation-eof-v1/bootanimation',
 'bootanimation-launcher':'bootanimation-vulkan-adapter-v1/bootanimation-launcher',
 'libsheng_boot_vulkan.so':'bootanimation-vulkan-adapter-v1/libsheng_boot_vulkan.so',
 'bootpic.zip':'bootanimation-diagnostic-v1/bootpic.zip',
 'apply-rosen-handle.sh':'rosen-ohos-handle-flag-v1/apply-ram.sh'}
for target,source in assets.items():shutil.copy2(r/'compat/sheng-graphics'/source,dest/target)
(dest/'bootanimation-diagnostic.json').write_text(json.dumps({'cust.bootanimation.pics':'/data/local/tmp/sheng-graphics/bootpic.zip','cust.bootanimation.video':'','cust.bootanimation.sounds':'','cust.bootanimation.duration':'20'})+'\n',encoding='utf-8')
g=(r/'tools/archive/probe_graphics_v43.inc').read_text(encoding='utf-8')
helper='''static int graphics_patch_native_handle(void) {
    int output[2];if(pipe(output)<0)return -1;
    pid_t child=fork();if(child<0){close(output[0]);close(output[1]);return -1;}
    if(child==0){close(output[0]);dup2(output[1],1);dup2(output[1],2);close(output[1]);
        execl("/busybox","busybox","sh","/graphics/apply-rosen-handle.sh",(char*)0);_exit(127);}
    close(output[1]);char text[1024];ssize_t n;
    while((n=read(output[0],text,sizeof(text)))>0)emit(text,(size_t)n);
    close(output[0]);int status;while(waitpid(child,&status,0)<0){if(errno!=EINTR)return -1;}
    if(!WIFEXITED(status)||WEXITSTATUS(status)!=0){note("Native handle patch rejected status=%d",status);return -1;}
    return 0;
}
'''
g=g.replace('static int graphics_ram_root(void) {',helper+'static int graphics_ram_root(void) {')
marker='    DIR *firmware=opendir("/stock-gpu-firmware");'
assert marker in g
stage='''    const char *boot_assets[]={"bootanimation-real","bootanimation-launcher","libsheng_boot_vulkan.so","bootpic.zip"};
    for(unsigned i=0;i<sizeof(boot_assets)/sizeof(boot_assets[0]);i++){
        char source[256],target[256];snprintf(source,sizeof(source),"/graphics/%s",boot_assets[i]);
        snprintf(target,sizeof(target),"/hmos-root/data/local/tmp/sheng-graphics/%s",boot_assets[i]);
        if(copy_ram_asset(source,target,0755)<0)return -1;
    }
    if(copy_ram_asset("/graphics/bootanimation-launcher","/hmos-root/system/bin/bootanimation",0755)<0||
       copy_ram_asset("/graphics/bootanimation-diagnostic.json","/hmos-root/sys_prod/etc/bootanimation/bootanimation_custom_config.json",0644)<0)return -1;
    const char *boot_log="/hmos-root/data/local/tmp/sheng-graphics/bootanimation-adapter.log";
    if(textfile(boot_log,"")<0||chown(boot_log,1003,1003)<0||chmod(boot_log,0600)<0)return -1;
    if(graphics_patch_native_handle()<0)return -1;
'''
g=g.replace(marker,stage+marker)
(r/'tools/probe_graphics.inc').write_text(g,encoding='utf-8')
(r/'tools/build_probe_v44.py').write_text((r/'tools/build_probe_v43.py').read_text(encoding='utf-8').replace('v43','v44'),encoding='utf-8')
(r/'tools/verify_v44.py').write_text((r/'tools/verify_v43.py').read_text(encoding='utf-8').replace('v43','v44'),encoding='utf-8')
report={'status':'candidate_not_flashed','boot_role':boot,'native_render_required_input_sha256':'0a699e2317dab4699117a90e7e21d5727bd823e3474a70ebaed4d32667e519ff','native_render_expected_patched_sha256':'d423413ec1fc58f40c5b04846b00530a4d82d0929eee769ede3bf5c605e5a77d','assets':{x:hashlib.sha256((dest/x).read_bytes()).hexdigest() for x in list(assets)+['bootanimation-diagnostic.json']},'scope':'Original init identity + EOF fix + original Vulkan SetSkContext adapter + private OHOS external handle flag interoperability; explicit gated diagnostic, not desktop. Known original Turnip v1 kept.'}
(r/'analysis/v44-native-inputs.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
print(json.dumps(report,indent=2))
