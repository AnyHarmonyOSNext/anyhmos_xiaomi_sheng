#!/busybox sh
# Explicit diagnostic entry, not automatically invoked by the v99 UI bootstrap.
set -eu
B=/busybox
P=/hmos-root/compat/bin
stage=firmware
trap 'code=$?; echo "WIFI_START_EXIT=$code STAGE=$stage"' EXIT
$B cat /proc/sys/kernel/random/boot_id /proc/uptime
$B sh "$P/stage-wifi-ram.sh"
$B tar -xzf "$P/official303-wlan-configs.tar.gz" -C /compat/firmware
stage=platform
$B sh "$P/load-official303-cnss2.sh"
stage=transport
$B sh "$P/load-official303-qrtr-mhi.sh"
stage=calibration
echo 1 > /sys/kernel/cnss/fs_ready
# Main driver registration waits for the same calibration completion in CNSS.
stage=driver
$B sh "$P/load-official303-qca_cld3_kiwi_v2.sh"
[ -e /sys/class/net/wlan0 ] || exit 40
echo WIFI_KERNEL_NETDEV_READY=1
stage=native-services
$B chroot /hmos-root /system/bin/param set sheng.debug.start.wifi true
echo WIFI_NATIVE_SERVICES_REQUESTED=1
stage=complete
