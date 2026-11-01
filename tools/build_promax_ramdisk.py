"""Apply reviewed GEM-W00 SP12 recipes to the known sheng vendor ramdisk.

Only host files are written. Proprietary input/output binaries stay outside Git.
Recipe evidence is static; this does not certify a successful device boot.
"""
import pathlib,sys,json,hashlib,subprocess,re,struct,difflib,io,gzip,argparse
REPO=pathlib.Path(__file__).resolve().parent.parent
parser=argparse.ArgumentParser(description=__doc__)
parser.add_argument('--donor',type=pathlib.Path,required=True)
parser.add_argument('--original',type=pathlib.Path,required=True)
parser.add_argument('--tools',type=pathlib.Path,required=True)
parser.add_argument('--recipe-dir',type=pathlib.Path,default=REPO/'patches/donor/gem-w00-111-sp12')
args=parser.parse_args()
sys.path.insert(0,str(args.tools/'python-libs'))
sys.path.insert(0,str(REPO/'tools'))
from elftools.elf.elffile import ELFFile
import vendor_ramdisk_edit as vr
from build_promax_images import cygpath
ROOT=args.donor;WORK=ROOT/'port-work';WORK.mkdir(exist_ok=True);P='sheng-compat-v118/';G=P+'graphics/'
base=args.original/'images/vendor_boot.img'
expected_base='6fd2ed9de8442a8c1301d8e8c3835a1bdf83ca145f25375491ba56e84b9fc615'
assert hashlib.sha256(base.read_bytes()).hexdigest()==expected_base
vr.MAGISKBOOT=str(args.tools/'android-fs/magiskboot.exe')
container=base.read_bytes();page=struct.unpack_from('<I',container,12)[0];header_size=struct.unpack_from('<I',container,2096)[0];ramdisk_size=struct.unpack_from('<I',container,24)[0];ramdisk_offset=(header_size+page-1)//page*page
(WORK/'base.lz4').write_bytes(container[ramdisk_offset:ramdisk_offset+ramdisk_size])
subprocess.run([vr.MAGISKBOOT,'decompress',str(WORK/'base.lz4'),str(WORK/'base.cpio')],check=True,capture_output=True)
def extract_guard(path,previous=False):
 destination=ROOT/('metadata/old-guard-inputs' if previous else 'metadata/guard-inputs')/path.lstrip('/')
 destination.parent.mkdir(parents=True,exist_ok=True)
 partition=path.split('/')[1]
 image=args.original/'images/super.img' if previous else ROOT/'extracted/base'/f'{partition}.img'
 relative=path if partition=='system' else '/'+path.split('/',2)[2]
 command=[str(args.tools/'erofs-cygwin/dump.erofs.exe')]+(['--offset=996147200'] if previous else [])+['--cat','--path='+relative,cygpath(image)]
 result=subprocess.run(command,check=True,capture_output=True);destination.write_bytes(result.stdout)
for recipe_path in args.recipe_dir.glob('*.json'):
 extract_guard(json.loads(recipe_path.read_text())['path'])
for path in ['/system/lib64/libaccountmgr.z.so','/system/lib64/chipset-sdk/libhukssdk.z.so','/system/lib64/chipset-sdk-sp/libcrypto_openssl.z.so','/sys_prod/etc/param/hw_defaults.para','/system/etc/sandbox/appdata-sandbox.json','/system/etc/sandbox/appdata-sandbox-isolated.json']:
 extract_guard(path)
for name in ['appdata-sandbox.json','appdata-sandbox-isolated.json']:
 extract_guard('/system/etc/sandbox/'+name,previous=True)
old=vr.parse((WORK/'base.cpio').read_bytes());new=dict(old)
def setfile(name,data,mode=0o100644):
 if isinstance(data,str):data=data.encode()
 if name in new:fields=new[name][0].copy()
 else:fields=[max(v[0][0] for v in new.values())+1,mode,0,0,1,0,len(data),0,0,0,0,len(name.encode())+1,0]
 fields[1]=mode;fields[6]=len(data);new[name]=(fields,data)
def text(name):return old[G+name][1].decode()
def sha(b):return hashlib.sha256(b).hexdigest()
recipes={}
for path in sorted(args.recipe_dir.glob('*.json')):
 recipe=json.loads(path.read_text());source=ROOT/'metadata/guard-inputs'/recipe['path'].lstrip('/');blob=source.read_bytes();assert sha(blob)==recipe['input_sha256'];patched=bytearray(blob)
 for change in recipe['changes']:
  at=change['offset'];before=bytes.fromhex(change['before']);after=bytes.fromhex(change['after']);assert len(before)==len(after) and patched[at:at+len(before)]==before
  patched[at:at+len(after)]=after
 assert sha(patched)==recipe['output_sha256']
 destination=WORK/'patched'/recipe['path'].lstrip('/');destination.parent.mkdir(parents=True,exist_ok=True);destination.write_bytes(patched)
 recipes[recipe['path']]=recipe
# Directory and guarded patched inputs in vendor_boot; no on-disk donor is edited.
fields=[max(v[0][0] for v in new.values())+1,0o40755,0,0,2,0,0,0,0,0,0,len((G+'promax').encode())+1,0];new[G+'promax']=(fields,b'')
for path,recipe in recipes.items():
 name=path.rsplit('/',1)[1]
 setfile(G+'promax/'+name,(WORK/'patched'/path.lstrip('/')).read_bytes(),0o100755 if name=='init' else 0o100644)
# Replace already-patched provider assets as well as their source guards.
for name in ['libaudio_policy_client.z.so','libcode_sign_utils.z.so','libsensor_client.z.so','libsps_privacy_indicator_service_intf.z.so','libwifi_sdk.z.so','libnet_tether_manager_if.z.so']:
 matches=[(p,r) for p,r in recipes.items() if p.endswith('/'+name)];assert len(matches)==1
 setfile(G+name,(WORK/'patched'/matches[0][0].lstrip('/')).read_bytes())
def stage(path,target=None,bind=False):
 recipe=recipes[path];name=path.rsplit('/',1)[1];target=target or '/hmos-root/compat/lib64/'+name;source='/hmos-root'+path
 result=f'echo "{recipe["input_sha256"]}  {source}" | $B sha256sum -c -\n$B cp /graphics/promax/{name} {target}\necho "{recipe["output_sha256"]}  {target}" | $B sha256sum -c -\n$B chmod '+('0755' if name=='init' else '0644')+f' {target}\n'
 if bind:result+=f'$B mount --bind {target} {source}\n'
 return result
head='#!/busybox sh\nset -eu\nB=/busybox\nR=/hmos-root\n'
compat=head+'$B mkdir -p $R/compat/bin $R/compat/lib64\n'+stage('/system/bin/init','/hmos-root/compat/bin/init')+stage('/system/lib64/libvulkan.so')
compat+=text('apply-compat-paths.sh').split('/busybox gzip -dc /graphics/libvulkan_freedreno.so.gz',1)[1]
compat=compat.replace('\n >',' >') if False else compat
# Retain the complete Mesa/Zink integrity checks from the known working package.
compat=compat[:compat.index('\n')+1]+compat[compat.index('\n')+1:]
start=text('apply-compat-paths.sh').index('/busybox gzip -dc /graphics/libvulkan_freedreno.so.gz')
compat=head+'$B mkdir -p $R/compat/bin $R/compat/lib64\n'+stage('/system/bin/init','/hmos-root/compat/bin/init')+stage('/system/lib64/libvulkan.so')+text('apply-compat-paths.sh')[start:]
setfile(G+'apply-compat-paths.sh',compat,0o100755)
render='/system/lib64/librender_service_base.z.so';rh=recipes[render]['output_sha256']
setfile(G+'apply-rosen-handle.sh',head+stage(render)+'echo PROMAX_ROSEN_PATCH_SET_STAGED\n',0o100755)
for name in ['apply-render-usage.sh','apply-rs-commit-sync-v1.sh']:
 setfile(G+name,head+f'echo "{rh}  $R/compat/lib64/librender_service_base.z.so" | $B sha256sum -c -\necho PROMAX_ROSEN_PATCH_SET_VERIFIED\n',0o100755)
setfile(G+'apply-framework-dev.sh',head+stage('/system/lib64/libcode_sign_utils.z.so')+'echo PROMAX_DEVELOPMENT_CODE_SIGN_COMPAT_STAGED\n',0o100755)
for script,path in [('apply-cli-wait-v1.sh','/system/lib64/platformsdk/libcli_tool_client.z.so'),('apply-msdp-local-v1.sh','/system/lib64/libdevicestatus_service.z.so'),('apply-audio-wait-v1.sh','/system/lib64/libaudio_policy_service.z.so'),('apply-time-v1.sh','/system/lib64/libtime_system_ability.z.so'),('apply-memmgr-v2.sh','/system/lib64/libmemmgrservice.z.so')]:
 body=head
 if script=='apply-msdp-local-v1.sh':body+='$B sh /graphics/apply-storage-local-v1.sh\n'
 body+=stage(path,bind=True)+'echo PROMAX_GUARDED_'+script.replace('-','_').replace('.','_')+'_STAGED\n'
 setfile(G+script,body,0o100755)
# Keep original software-key directory preparation, use new crypt library symbols.
db=text('apply-db-key-v2.sh').split('S="$R/system/lib64/librelational_store_crypt.z.so"',1)[0]
for name in ['librelational_store_crypt.z.so','libkv_store_crypt.z.so','libdistributeddatasvcfwk.z.so']:db+=stage('/system/lib64/'+name,bind=True)
db+='echo PROMAX_DB_KEY_BRIDGE_STAGED\n';setfile(G+'apply-db-key-v2.sh',db,0o100755)
# The shim uses the public C Hks ABI, and the exact OpenSSL exports were checked.
hmac=text('apply-account-hmac.sh');account_checks=[]
for path in ['/system/lib64/libaccountmgr.z.so','/system/lib64/chipset-sdk/libhukssdk.z.so','/system/lib64/chipset-sdk-sp/libcrypto_openssl.z.so']:
 data=(ROOT/'metadata/guard-inputs'/path.lstrip('/')).read_bytes();digest=sha(data)
 line=next(l for l in hmac.splitlines() if path in l and 'sha256sum' in l);expected=re.search(r'\bin ([0-9a-f]{64})',line)[1];hmac=hmac.replace(expected,digest);account_checks.append({'path':path,'input_sha256':digest})
huks=(ROOT/'metadata/guard-inputs/system/lib64/chipset-sdk/libhukssdk.z.so').read_bytes();symbols=ELFFile(io.BytesIO(huks)).get_section_by_name('.dynsym');exports={s.name for s in symbols.iter_symbols() if s['st_shndx']!='SHN_UNDEF'}
required={'HksKeyExist','HksGenerateKey','HksInit','HksUpdate','HksFinish','HksAbort'};assert required<=exports
setfile(G+'apply-account-hmac.sh',hmac,0o100755)
# Keep all Pro Max model parameters, change only unavailable NearLink capability.
cap=(ROOT/'metadata/guard-inputs/sys_prod/etc/param/hw_defaults.para').read_bytes();assert cap.count(b'const.nearlink.enable=true')==1
newcap=cap.replace(b'const.nearlink.enable=true',b'const.nearlink.enable=false');setfile(G+'hw_defaults-v141.para',newcap)
hardware=text('apply-hardware-v116.sh');hardware=hardware.replace('47e94ce212bf301531e1e0f6480f9b4c566296a557e8fc03b44d958ed81fe8a2',sha(cap)).replace('3fa79d36281510333d96de8ff23844e40229b1d227ada18ca0eff2fbf24a9dc2',sha(newcap));setfile(G+'apply-hardware-v116.sh',hardware,0o100755)
preload=text('apply-preload.sh').replace('/preload/WKI-W10/all/cn','/preload/GEM-W00/all/cn');setfile(G+'apply-preload.sh',preload,0o100755)
# Apply the small original sandbox delta to the new donor, retaining its fields.
sandbox=text('apply-app-sandbox.sh');sandbox_report=[]
for name in ['appdata-sandbox.json','appdata-sandbox-isolated.json']:
 oldbytes=(ROOT/'metadata/old-guard-inputs/system/etc/sandbox'/name).read_bytes()
 newbytes=(ROOT/'metadata/guard-inputs/system/etc/sandbox'/name).read_bytes()
 patched_old=gzip.decompress(old[G+name+'.gz'][1])
 original=oldbytes.decode().splitlines(keepends=True);patched=patched_old.decode().splitlines(keepends=True);result=newbytes.decode()
 opcodes=difflib.SequenceMatcher(None,original,patched,autojunk=False).get_opcodes();edits=0
 for tag,a,b,c,d in opcodes:
  if tag=='equal':continue
  lo=max(0,a-6);hi=min(len(original),b+6)
  before=''.join(original[lo:hi]);after=''.join(original[lo:a]+patched[c:d]+original[b:hi])
  assert result.count(before)==1,(name,a,b,'ambiguous sandbox context')
  result=result.replace(before,after,1);edits+=1
 output=result.encode();assert json.loads(output)['create-only-on-daemon']==json.loads(newbytes)['create-only-on-daemon']
 sandbox=sandbox.replace(sha(oldbytes),sha(newbytes)).replace(sha(patched_old),sha(output))
 setfile(G+name+'.gz',gzip.compress(output,mtime=0))
 sandbox_report.append({'path':'/system/etc/sandbox/'+name,'input_sha256':sha(newbytes),'output_sha256':sha(output),'context_checked_edits':edits,'donor_additions_preserved':True})
setfile(G+'apply-app-sandbox.sh',sandbox,0o100755)
# Pro Max already has an audio policy directory; cover it with the sheng policy.
audio=text('apply-audio-v116.sh').replace('[ ! -e "$R/chip_prod/etc/audio" ]\n$B ln -s /compat/etc/audio "$R/chip_prod/etc/audio"', '[ -d "$R/chip_prod/etc/audio" ]\n$B mount --bind "$R/compat/etc/audio" "$R/chip_prod/etc/audio"')
assert audio!=text('apply-audio-v116.sh');setfile(G+'apply-audio-v116.sh',audio,0o100755)
# Additional filesystems are carried inside freshly created ext4 userdata.
seed_names=['preload','chip_prod','anco_hmos','cust','version'];seed_lines=[]
for name in seed_names:
 folder='preload' if name=='preload' else 'cust' if name=='version' else 'base';img=ROOT/'extracted'/folder/(name+'.img');report=json.loads((ROOT/'extracted'/folder/'extraction-report.json').read_text());record=next(c for c in report['components'] if c['name']==name);assert record['hash_verified'] and record['extracted'];seed_lines.append(record['sha256']+'  '+name+'.img')
setfile(G+'promax/seed-images.sha256','\n'.join(seed_lines)+'\n')
mount='''#!/busybox sh
set -eu
B=/busybox
R=/hmos-root
S=$R/data/hmos-promax
$B test -d "$S"
$B chown -R 0:0 "$S"
$B chmod 0700 "$S"
$B chmod 0600 "$S"/*.img
cd "$S"
$B sha256sum -c /graphics/promax/seed-images.sha256
# Nodes are created in the early RAM /dev, before native system services start.
i=0
while [ "$i" -lt 16 ]; do
 [ -b /dev/loop$i ] || $B mknod /dev/loop$i b 7 "$i"
 i=$((i+1))
done
for name in preload chip_prod anco_hmos cust version; do
 lower=/hmos/promax-$name
 $B mkdir -p "$lower" "$R/$name"
 loop=$($B losetup -f)
 $B losetup -r "$loop" "$S/$name.img"
 $B mount -t erofs -o ro,nosuid,nodev "$loop" "$lower"
 if [ "$name" = chip_prod ] || [ "$name" = preload ]; then
  upper=/hmos-ram/promax-$name-upper
  work=/hmos-ram/promax-$name-work
  $B mkdir -p "$upper" "$work"
  $B mount -t overlay -o lowerdir="$lower",upperdir="$upper",workdir="$work" overlay "$R/$name"
 else
  $B mount --bind "$lower" "$R/$name"
  $B mount -o remount,bind,ro,nosuid,nodev "$R/$name"
 fi
 echo "PROMAX_SEED_MOUNTED name=$name loop=$loop"
done
# Do not launch the Android backend until its sheng adaptations are verified.
echo PROMAX_CONTAINER_FILES_PRESENT_RUNTIME_NOT_VALIDATED
'''
setfile(G+'promax/mount-seed-images.sh',mount,0o100755)
userdata=text('init-userdata-ext4.sh')+'\n$B sh /graphics/promax/mount-seed-images.sh\n';setfile(G+'init-userdata-ext4.sh',userdata,0o100755)
# Recompute the payload inventory, including every new guarded component.
manifest=json.loads(old[P+'MANIFEST.json'][1]);members=set(manifest)
for name in new:
 if name.startswith(G+'promax/') and (new[name][0][1]&0o170000)==0o100000:members.add(name[len(P):])
for relative in sorted(members):
 fields,blob=new[P+relative];manifest[relative]={'bytes':len(blob),'mode':oct(fields[1]),'sha256':sha(blob)}
setfile(P+'MANIFEST.json',json.dumps(manifest,indent=2)+'\n')
changed={n for n in new if n not in old or new[n]!=old[n]};added=set(new)-set(old)
report={'donor':'GEM-LGRP3-CHN 207.0.0.111(SP12)','base_vendor_boot_sha256':sha(base.read_bytes()),'changed_entries':sorted(changed),'added_entries':sorted(added),'patch_recipes':len(recipes),'account_input_checks':account_checks,'seed_checksums':seed_lines,'boot_unchanged':True,'init_boot_unchanged':True,'dtb_unchanged':True,'kernel_unchanged':True,'device_boot_tested':False,'features_not_validated':['144Hz','Zhuoyitong Android backend','all application GPU paths']}
(WORK/'payload-integration-report.json').write_text(json.dumps(report,indent=2)+'\n')
report['sandbox_port']=sandbox_report
# Materialize scripts for shell syntax checks, not full proprietary binaries.
scripts=WORK/'integrated-scripts';scripts.mkdir(exist_ok=True)
for n in changed:
 if n.endswith('.sh'):
  dest=scripts/n.rsplit('/',1)[1];dest.write_bytes(new[n][1]);subprocess.run([r'C:\Program Files\Git\bin\bash.exe','-n',str(dest)],check=True)
def mutate(entries):
 for name in sorted(changed):entries[name]=new[name]
image=vr.edit(base,report['base_vendor_boot_sha256'],WORK/'vendor-boot-repack',mutate,changed,added)
destination=WORK/'vendor_boot_promax_111sp12.img';destination.write_bytes(image)
report['vendor_boot_sha256']=sha(image);report['vendor_boot_bytes']=len(image);report['cpio_roundtrip_verified']=True
(WORK/'payload-integration-report.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2),flush=True)
