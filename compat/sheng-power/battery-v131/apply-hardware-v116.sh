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
