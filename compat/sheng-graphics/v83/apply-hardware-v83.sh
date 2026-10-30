#!/bin/sh
set -eu
B=/busybox
R=/hmos-root
$B mkdir -p $R/compat/etc $R/compat/bin
for name in init-hardware-v83.cfg displaymgr-profile.json; do
 $B cp /graphics/$name $R/compat/etc/$name
 $B chmod 0644 $R/compat/etc/$name
done
for name in sheng_hardware_display hardware_observe; do
 $B cp /graphics/$name $R/compat/bin/$name
 $B chmod 0755 $R/compat/bin/$name
done
# Only the actual composer host group receives hardware backlight write access.
$B chown 0:3036 /sys/class/backlight/panel0-backlight/brightness
$B chmod 0660 /sys/class/backlight/panel0-backlight/brightness
$B mkdir -p $R/data/service/el0/stats $R/data/service/el0/thermal/config
$B chown -R 5528:5528 $R/data/service/el0/stats $R/data/service/el0/thermal
echo SHENG_V83_DISPLAY_AND_HARDWARE_SERVICES_STAGED_VENDOR_UNTOUCHED
