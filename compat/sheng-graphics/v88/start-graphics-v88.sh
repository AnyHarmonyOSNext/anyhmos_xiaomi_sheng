set -e
B=/busybox
R=/hmos-root
for n in gpucc-kalama msm_performance qcom_va_minidump coresight msm_kgsl; do
 mod=$(echo "$n" | $B tr - _); if ! $B grep -q "^$mod " /proc/modules; then $B insmod "$R/vendor_dlkm/lib/modules/$n.ko"; fi
done
nums=$($B cat /sys/class/kgsl/kgsl-3d0/dev)
if [ ! -c $R/dev/kgsl-3d0 ]; then $B mknod $R/dev/kgsl-3d0 c "${nums%:*}" "${nums#*:}"; fi
$B chown 0:1003 $R/dev/kgsl-3d0
$B chmod 0660 $R/dev/kgsl-3d0
$B chroot $R /system/bin/param get sheng.debug.start.coredeps
$B chroot $R /system/bin/param set sheng.debug.start.gpu-policy true
$B sleep 2
$B chroot $R /system/bin/param set sheng.debug.start.render true
$B chroot $R /system/bin/param set sheng.debug.start.installs true
$B sleep 2
$B ps | $B grep -E 'host|render_service|accesstoken|installs'
$B ls -ld $R/data/service/el1/public/access_token
$B chroot $R /system/bin/hilog -x -T SAFWK | $B tail -15