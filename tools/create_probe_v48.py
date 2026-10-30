"""Persist the device-tested BMS filesystem and AnyHarmonyOS developer patch."""
from pathlib import Path
import shutil,json

r=Path(__file__).resolve().parent.parent
for name in ['hmos_probe.c','probe_graphics.inc','probe_command.inc']:
    archive=r/'tools/archive'/(Path(name).stem+'_v47'+Path(name).suffix)
    if not archive.exists():shutil.copy2(r/'tools'/name,archive)
dst=r/'compat/sheng-graphics/v48'
shutil.copytree(r/'compat/sheng-graphics/v47',dst,dirs_exist_ok=True)
c=(r/'tools/archive/hmos_probe_v47.c').read_text().replace('v47','v48')
old='ram_mount("/hmos-ram","mode=0755,size=256m")'
assert c.count(old)==1
c=c.replace(old,'ram_mount("/hmos-ram","mode=0755,size=2048m")')
needle='    const char *state_dirs[]='
assert c.count(needle)==1
c=c.replace(needle,'    /* RAM ext4 supplies real xattrs for the native framework; no userdata. */\n'
    '    if(graphics_run_script("/graphics/init-ram-ext4.sh")<0)return -1;\n'+needle)
needle='"/hmos-root/data/local/tmp"};'
assert c.count(needle)==1
c=c.replace(needle,'"/hmos-root/data/local/tmp","/hmos-root/data/service/el1/public",'
    '"/hmos-root/data/app/el1","/hmos-root/data/storage/el1",'
    '"/hmos-root/data/storage/el2"};')
(r/'tools/hmos_probe.c').write_text(c)
g=(r/'tools/archive/probe_graphics_v47.inc').read_text()
needle='    if(graphics_run_script("/graphics/apply-compat-paths.sh")<0||graphics_run_script("/graphics/apply-rosen-handle.sh")<0)return -1;'
assert g.count(needle)==1
g=g.replace(needle,needle+'\n    if(graphics_run_script("/graphics/apply-framework-dev.sh")<0)return -1;')
(r/'tools/probe_graphics.inc').write_text(g)
# mke2fs resolves a newly created regular file inside the donor chroot.
# Its overlay upper directory is our private tmpfs; no block device is formatted.
script='''#!/bin/sh
set -eu
B=/busybox
R=/hmos-root
P="$R/compat/framework-data.ext4"
$B grep -q ' /hmos-ram tmpfs ' /proc/mounts
$B grep -q ' /hmos-root overlay ' /proc/mounts
$B test ! -e "$P"
$B mkdir -p "$R/compat"
$B truncate -s 1536M "$P"
$B chroot "$R" /system/bin/mke2fs -q -F -t ext4 -O verity,^orphan_file -E lazy_itable_init=0,lazy_journal_init=0 /compat/framework-data.ext4
$B test ! -e /sys/class/block/loop7/loop/backing_file
nums=$($B cat /sys/class/block/loop7/dev)
if [ ! -b /dev/loop7 ]; then $B mknod /dev/loop7 b "${nums%:*}" "${nums#*:}"; fi
$B losetup /dev/loop7 "$P"
$B umount "$R/data"
$B mount -t ext4 -o nosuid,nodev,noatime /dev/loop7 "$R/data"
$B chmod 0771 "$R/data"
echo HMOS_RAM_EXT4_DATA_READY_NO_PHYSICAL_USERDATA
$B grep " $R/data " /proc/mounts
'''
(dst/'init-ram-ext4.sh').write_bytes(script.encode('utf-8'))
(dst/'apply-framework-dev.sh').write_bytes('''#!/bin/sh
set -eu
B=/busybox
R=/hmos-root
p="$R/system/lib64/libcode_sign_utils.z.so"
h=$($B sha256sum "$p")
case "$h" in bbd86eec0b55323d61f6f27a7e3c132f7e7fbcdf3820f723d2db7dee40b0b4a9*) ;; *) echo CODE_SIGN_DONOR_MISMATCH; exit 41;; esac
q="$R/compat/lib64/libcode_sign_utils.z.so"
$B test ! -e "$q"
$B cp /graphics/libcode_sign_utils.z.so "$q"
h=$($B sha256sum "$q")
case "$h" in 4ca57938aa23ed1dd4fd585bd411f12ab9a8540f804afe4c30383fff17071364*) ;; *) echo CODE_SIGN_OUTPUT_MISMATCH; exit 42;; esac
$B chmod 0644 "$q"
echo HMOS_ANYHARMONY_DEVELOPMENT_FSVERITY_COMPAT_NO_KERNEL_INTEGRITY_CLAIM
'''.encode('utf-8'))
shutil.copy2(r/'compat/sheng-framework/anyharmony-fsverity-dev-v1/libcode_sign_utils.z.so',dst/'libcode_sign_utils.z.so')
shutil.copy2(r/'compat/sheng-framework/anyharmony-fsverity-dev-v1/patch.json',dst/'framework-dev-patch.json')
cfg=json.loads((r/'tools/configs/init-core-v47.cfg').read_text())
pre=next(j for j in cfg['jobs'] if j['name']=='pre-init')['cmds']
index=pre.index('load_persist_params ')
pre.insert(index+1,'setparam persist.bms.test-upgrade false')
pre.insert(index+2,'mkdir /data/service/el1/public 0711 root root')
core=next(j for j in cfg['jobs'] if j['name']=='param:sheng-debug-coredeps')['cmds']
core.insert(1,'restorecon -F /data/service/el1/public/access_token')
(r/'tools/configs/init-core-v48.cfg').write_text(json.dumps(cfg,indent=2)+'\n')
for a,b in [('build_probe_v47.py','build_probe_v48.py'),('verify_v47.py','verify_v48.py')]:
    (r/'tools'/b).write_text((r/'tools'/a).read_text().replace('v47','v48'))
report={'version':'v48','state':'OFFLINE_CANDIDATE_NOT_FLASHED',
 'changes':['RAM-backed 1536MiB ext4 /data; kernel xattrs and ACLs, no physical userdata',
 'private AnyHarmonyOS exact-byte fsverity development compatibility with donor SHA guards',
 'persist.bms.test-upgrade false from AnyHarmonyOS; retain native roles and permissions'],
 'v46_runtime_evidence':'v46-anyharmony-app-core-hilog-20261027-2216.txt.gz: SetSecurityLabel/GetRdbStore/VerifyCode errors absent for tested processes; scanning proceeds; BMS401 not yet published',
 'not_done':['cold boot acceptance','full automatic GPU/service startup','desktop','default screenshot API','touch','WiFi'],
 'vendor':'read-only; no overlays or vendor-path replacements'}
(r/'analysis/v48-framework.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps(report,indent=2))
