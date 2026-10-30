#!/bin/sh
set -eu
B=/busybox
R=/hmos-root
$B mkdir -p $R/compat/etc $R/compat/bin
for name in init-hardware-v116.cfg powermgr.json; do
 $B cp /graphics/$name $R/compat/etc/$name
 $B chmod 0644 $R/compat/etc/$name
done
for name in sheng_hardware_display hardware_observe native_brightness_launcher native_sa_check native_battery_hdi_publisher_v131; do
 $B cp /graphics/$name $R/compat/bin/$name
 $B chmod 0755 $R/compat/bin/$name
done
# Only the actual composer host group receives hardware backlight write access.
$B chown 0:3036 /sys/class/backlight/panel0-backlight/brightness
$B chmod 0660 /sys/class/backlight/panel0-backlight/brightness
$B mkdir -p $R/data/service/el0/stats $R/data/service/el0/thermal/config
$B chown -R 5528:5528 $R/data/service/el0/stats $R/data/service/el0/thermal
echo SHENG_V102_DISPLAY_AND_HARDWARE_SERVICES_STAGED_VENDOR_UNTOUCHED

: > $R/data/local/tmp/sheng-brightness-stderr.txt
$B chown 5528:5528 $R/data/local/tmp/sheng-brightness-stderr.txt
$B chmod 0600 $R/data/local/tmp/sheng-brightness-stderr.txt

: > $R/data/local/tmp/sheng-composer-metrics.txt
$B chown 3036:3036 $R/data/local/tmp/sheng-composer-metrics.txt
$B chmod 0640 $R/data/local/tmp/sheng-composer-metrics.txt

$B touch $R/data/local/tmp/sheng-gpu-policy-disabled

: > $R/data/local/tmp/sheng-battery-hdi.txt
$B chown 3025:3025 $R/data/local/tmp/sheng-battery-hdi.txt
$B chmod 0600 $R/data/local/tmp/sheng-battery-hdi.txt

# Only wifi_host receives this adapter; original vendor libraries remain intact.
$B mkdir -p $R/compat/lib64
$B cp /graphics/libsheng_wifi_category_v134.so $R/compat/lib64/libsheng_wifi_category_v134.so
$B chmod 0644 $R/compat/lib64/libsheng_wifi_category_v134.so
: > $R/data/local/tmp/sheng-wifi-category-v134.txt
$B chown 3026:3026 $R/data/local/tmp/sheng-wifi-category-v134.txt
$B chmod 0600 $R/data/local/tmp/sheng-wifi-category-v134.txt

# Keep Boot Control isolated from the original vendor and the HMOS linker.
$B mkdir -p /compat/bootcontrol-v135
$B cp /sheng-compat-v118/bootcontrol-v135/* /compat/bootcontrol-v135/
$B chmod 0644 /compat/bootcontrol-v135/*

# Bluetooth remains isolated from both the vendor partition and its linker.
$B mkdir -p /compat/bluetooth-v136 $R/compat/bluetooth-v136/ohos
$B cp -R /sheng-compat-v118/bluetooth-v136/. /compat/bluetooth-v136/
# /compat is already the RAM root compat alias; do not copy onto itself.
$B cp /compat/bluetooth-v136/native_bt_hdi_publisher_v136 $R/compat/bin/
$B cp /compat/bluetooth-v136/native_bt_host_check_v138 $R/compat/bin/
$B cp /compat/bluetooth-v136/native_bt_host_check_v139 $R/compat/bin/
$B chmod 0755 $R/compat/bin/native_bt_host_check_v139
$B chmod 0755 $R/compat/bin/native_bt_host_check_v138
$B chmod 0755 $R/compat/bin/native_bt_hdi_publisher_v136
for file in init-bluetooth-v136.cfg bluetooth_service_v136.json; do
 $B cp /compat/bluetooth-v136/$file $R/compat/etc/$file
done
: > $R/data/local/tmp/sheng-bluetooth-hdi.txt
$B chown 3021:3021 $R/data/local/tmp/sheng-bluetooth-hdi.txt
$B chmod 0600 $R/data/local/tmp/sheng-bluetooth-hdi.txt

: > $R/data/local/tmp/sheng-bluetooth-check.txt
$B chown 2000:2000 $R/data/local/tmp/sheng-bluetooth-check.txt
$B chmod 0600 $R/data/local/tmp/sheng-bluetooth-check.txt

# Original SoftBus profile in the RAM system overlay.
$B cp /compat/bluetooth-v136/softbus_server.json $R/system/profile/softbus_server.json

# sheng has no NearLink hardware. Correct only the donor capability in RAM.
capability=$R/sys_prod/etc/param/hw_defaults.para
capability_sha=$($B sha256sum "$capability")
case "$capability_sha" in
 47e94ce212bf301531e1e0f6480f9b4c566296a557e8fc03b44d958ed81fe8a2*)
  $B cp /graphics/hw_defaults-v141.para "$capability"
  $B chmod 0644 "$capability"
  ;;
 3fa79d36281510333d96de8ff23844e40229b1d227ada18ca0eff2fbf24a9dc2*) ;;
 *) echo SHENG_V141_CAPABILITY_HASH_MISMATCH >&2; exit 1 ;;
esac
echo SHENG_V141_NEARLINK_UNSUPPORTED_RAM_CAPABILITY
