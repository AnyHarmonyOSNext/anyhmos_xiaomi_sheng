"""Integrate verified software UserAuth behind a separate original HDF host."""
from pathlib import Path
import shutil,json,subprocess
r=Path(__file__).resolve().parent.parent
for name in ['hmos_probe.c','probe_graphics.inc','probe_command.inc']:
 p=r/'tools'/name;q=r/'tools/archive'/(p.stem+'_v72'+p.suffix)
 if not q.exists():shutil.copy2(p,q)
d=r/'compat/sheng-graphics/v73'
shutil.copytree(r/'compat/sheng-graphics/v72',d,dirs_exist_ok=True)
# Retain old diagnostic binaries in v72; they are not required to boot v73.
drop=['platform_cpp_abi','buffer_vdi_contract','composer_vdi_contract','native_buffer_contract','rosen_gpu_contract','rosen_native_mode']
for name in drop:(d/name).unlink()
report=json.loads((r/'compat/sheng-framework/useriam-v1/manifest.json').read_text())
script=['set -e','B=/busybox','R=/hmos-root']
for name,meta in report['artifacts'].items():
 shutil.copy2(r/'compat/sheng-framework/useriam-v1'/(name+'.gz'),d/(name+'.gz'))
 target='$R/compat/'+('bin/' if name=='useriam_empty_contract' else 'lib64/')+name
 script += [f'$B gzip -dc /graphics/{name}.gz > {target}',f'echo "{meta["sha256"]}  {target}" | $B sha256sum -c -',f'$B chmod 0755 {target}']
script.append('echo SHENG_SOFTWARE_USERAUTH_4_1_STAGED_VENDOR_UNTOUCHED')
(d/'apply-useriam.sh').write_text('\n'.join(script)+'\n',newline='\n')
profile=json.loads((r/'work/hmos_system/system/system/profile/useriam.json').read_text())
profile['systemability']=[sa for sa in profile['systemability'] if sa['name'] in [901,921,931]]
assert len(profile['systemability'])==3
(d/'useriam-core.json').write_text(json.dumps(profile,indent=2)+'\n')
extra=json.loads((d/'init-desktop-services.cfg').read_text())
service=json.loads((r/'work/hmos_system/system/system/etc/init/useriam.cfg').read_text())['services'][0]
service.update(path=['/system/bin/sa_main','/compat/etc/useriam-core.json'],disabled=1,once=1,sandbox=0,saspawn=False)
service.pop('jobs',None)
extra['services'] += [service,dict(name='sheng_userauth_host',path=['/vendor/bin/hdf_devhost','-i','2','-n','sheng_userauth_host'],uid='useriam',gid=['useriam','uhdf_driver'],disabled=1,once=1,sandbox=0,**{'start-mode':'condition'})]
extra['jobs'] += [dict(name='param:sheng-useriam',condition='sheng.debug.start.useriam=true',cmds=[
 'mkdir /data/service/el1/public/useriam 0700 useriam useriam',
 'mkdir /data/service/el1/public/userauth 0700 useriam useriam',
 'start sheng_userauth_host','start useriam'])]
(d/'init-desktop-services.cfg').write_text(json.dumps(extra,indent=2)+'\n')
hcs=(r/'tools/configs/sheng-graphics.hcs').read_text()
assert hcs.endswith('    }\n}\n')
hcs=hcs[:-len('    }\n}\n')]+'''        sheng_userauth {
            hostName = "sheng_userauth_host";
            priority = 50;
            userauth_device {
                device0 {
                    policy = 2;
                    priority = 100;
                    moduleName = "/compat/lib64/libsheng_user_auth_driver.so";
                    serviceName = "user_auth_interface_service";
                    preload = 0;
                    permission = 0664;
                    deviceMatchAttr = "";
                }
            }
        }
    }
}
'''
source=r/'tools/configs/sheng-graphics-v73.hcs';source.write_text(hcs)
base='/mnt/c/SHENG_WORKSPACE'
subprocess.run(['wsl','-d','Ubuntu-22.04','--','/root/hmos-work/graphics-deps/hc-gen','-b','-o',base+'/compat/sheng-graphics/v73/hdf_default',base+'/tools/configs/sheng-graphics-v73.hcs'],check=True)
assert (d/'hdf_default.hcb').stat().st_size>(r/'compat/sheng-graphics/v72/hdf_default.hcb').stat().st_size
shutil.copy2(r/'tools/configs/init-core-v72.cfg',r/'tools/configs/init-core-v73.cfg')
p=r/'tools/probe_graphics.inc';s=p.read_text()
for name in drop:s=s.replace(',"'+name+'"','').replace('"'+name+'",','')
marker='    if(copy_ram_asset("/graphics/native_display_wake","/hmos-root/compat/bin/native_display_wake",0755)<0)return -1;'
assert s.count(marker)==1
s=s.replace(marker,marker+'\n    if(graphics_run_script("/graphics/apply-useriam.sh")<0||copy_ram_asset("/graphics/useriam-core.json","/hmos-root/compat/etc/useriam-core.json",0644)<0)return -1;')
p.write_text(s)
p=r/'tools/hmos_probe.c';p.write_text(p.read_text().replace('v72','v73'))
for name in ['build_probe','verify']:
 s=(r/f'tools/{name}_v72.py').read_text().replace('v72','v73')
 if name=='verify':s=s.replace("'sheng_display_wake'}","'sheng_display_wake','useriam','sheng_userauth_host'}")
 (r/f'tools/{name}_v73.py').write_text(s)
print('v73 staged: isolated software UserAuth4.1 host and original core useriam SAs')
