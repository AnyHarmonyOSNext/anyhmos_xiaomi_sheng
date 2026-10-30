set -e
B=/busybox
R=/hmos-root
$B cp /graphics/sheng_thp_bridge $R/compat/bin/sheng_thp_bridge
echo "e2a5487f4bee6f42389762929df0af69e2085de9617320d7b9552d431c5f178c  $R/compat/bin/sheng_thp_bridge" | $B sha256sum -c -
$B chmod 0755 $R/compat/bin/sheng_thp_bridge
$B cp /graphics/native_thp_launcher $R/compat/bin/native_thp_launcher
echo "2281a928f5850d48cad2145dda037407dd090463239e0aa375d12c31c33eb0b8  $R/compat/bin/native_thp_launcher" | $B sha256sum -c -
$B chmod 0755 $R/compat/bin/native_thp_launcher
$B cp /graphics/native_screenlock_request $R/compat/bin/native_screenlock_request
echo "bffd5494d4e8040c48fb8a1c496d7b9b73d0006de72935fa9a894d5670f93b8b  $R/compat/bin/native_screenlock_request" | $B sha256sum -c -
$B chmod 0755 $R/compat/bin/native_screenlock_request
: > $R/data/local/tmp/sheng-thp-service.txt
$B mkdir -p $R/data/local/tmp/sheng-capture
$B rm -f $R/data/local/tmp/sheng-capture/screenlock-cycle-test $R/data/local/tmp/sheng-capture/screenlock-callback-test
$B rm -f $R/data/local/tmp/sheng-capture/display0.jpeg $R/data/local/tmp/v97-autostart-desktop.jpeg
: > $R/data/local/tmp/sheng-capture/unlock-request.txt
$B chown 2000:2000 $R/data/local/tmp/sheng-capture/unlock-request.txt
$B touch $R/data/local/tmp/sheng-gpu-owner-cleanup
$B chmod 0644 $R/data/local/tmp/sheng-gpu-owner-cleanup
$B mkdir -p $R/compat/oobe-offline-v1
$B cp $R/sys_prod/etc/oobe/hwupgrade_extend_pages.json $R/compat/oobe-offline-v1/hwupgrade_extend_pages.json
$B cp /graphics/oobe_page_offline.json $R/compat/oobe-offline-v1/oobe_page.json
$B chmod 0755 $R/compat/oobe-offline-v1
$B chmod 0644 $R/compat/oobe-offline-v1/*.json
$B mount --bind $R/compat/oobe-offline-v1 $R/sys_prod/etc/oobe
for name in xiaomi-touch uinput; do
 nums=$($B cat /sys/class/misc/$name/dev)
 $B test ! -e $R/dev/$name
 $B mknod $R/dev/$name c "${nums%:*}" "${nums#*:}"
 $B chmod 0600 $R/dev/$name
done
$B test -f /proc/xm_htc_report_coordinate
echo 0 > /proc/xm_htc_report_coordinate
echo SHENG_V82_RUNTIME_STAGED_VENDOR_UNTOUCHED

$B sh /graphics/apply-hardware-v97.sh
