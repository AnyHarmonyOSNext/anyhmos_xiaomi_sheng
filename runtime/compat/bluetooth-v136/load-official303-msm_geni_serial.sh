#!/busybox sh
set -eu
B=/busybox
R=/hmos-root
M=$R/vendor_dlkm/lib/modules
[ "$($B uname -r)" = 5.15.178-android13-8-00021-g6f2f96be86b9-ab13729987 ] || exit 30
echo STOCK_MODULE_PLAN_BEGIN=msm_geni_serial
if $B grep -q '^msm_geni_serial ' /proc/modules; then
 echo MODULE_ALREADY_PRESENT=msm_geni_serial
else
 echo '509762d2fcb48dc89220e329383f3cad88b6b0e7a90184bf12e9fa45687550b9  '$M/msm_geni_serial.ko | $B sha256sum -c -
 echo MODULE_LOAD_BEGIN=msm_geni_serial.ko
 $B timeout 12 $B insmod $M/msm_geni_serial.ko || { code=$?; echo MODULE_LOAD_FAILED=msm_geni_serial.ko:$code; exit $code; }
 $B grep '^msm_geni_serial ' /proc/modules
fi
echo STOCK_MODULE_PLAN_COMPLETE=msm_geni_serial
