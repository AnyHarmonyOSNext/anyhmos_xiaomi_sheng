"""Make a bounded explicit RAM-only GPU stage from already verified inputs."""
from pathlib import Path
import json,hashlib
r=Path(__file__).resolve().parent.parent
mods=json.loads((r/'analysis/stock-gpu-abi-verification.json').read_text())
lines=['#!/busybox sh','set -eu','echo SHENG_GPU_STAGE_BEGIN']
for m in mods:
    name=m['module'];path='/hmos-root/vendor_dlkm/lib/modules/'+name+'.ko'
    lines += [f'test "$(/busybox sha256sum {path} | /busybox cut -d " " -f1)" = {m["sha256"]}',f'if ! /busybox grep -q "^{name.replace("-","_")} " /proc/modules; then /busybox insmod {path}; fi']
lib=r/'compat/sheng-graphics/gpu-v1/libvulkan_freedreno.so';sha=hashlib.sha256(lib.read_bytes()).hexdigest()
lines += ['pair=$(/busybox cat /sys/class/kgsl/kgsl-3d0/dev)','major=${pair%:*}; minor=${pair#*:}',
'if ! test -c /hmos-root/dev/kgsl-3d0; then /busybox mknod /hmos-root/dev/kgsl-3d0 c "$major" "$minor"; fi',
'/busybox chown 0:1003 /hmos-root/dev/kgsl-3d0','/busybox chmod 0660 /hmos-root/dev/kgsl-3d0',
'/busybox gzip -dc /hmos-root/data/local/tmp/sheng-graphics/libvulkan_freedreno.so.gz > /hmos-root/data/local/tmp/sheng-graphics/libvulkan_freedreno.so',
f'test "$(/busybox sha256sum /hmos-root/data/local/tmp/sheng-graphics/libvulkan_freedreno.so | /busybox cut -d " " -f1)" = {sha}',
'/busybox chmod 0755 /hmos-root/data/local/tmp/sheng-graphics/libvulkan_freedreno.so',
'echo SHENG_GPU_STAGE_READY',
'if test "${1:-native}" = stage-only; then exit 0; fi',
'/busybox chroot /hmos-root /data/local/tmp/sheng-graphics/native_buffer_contract /data/local/tmp/sheng-graphics/libvulkan_freedreno.so']
(r/'work/gpu-native-stage.sh').write_bytes(('\n'.join(lines)+'\n').encode('utf-8'))
print('GPU script prepared; target library SHA256',sha)
