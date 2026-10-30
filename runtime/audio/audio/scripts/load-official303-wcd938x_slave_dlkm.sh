#!/busybox sh
set -eu
B=/busybox
R=/hmos-root
M=$R/vendor_dlkm/lib/modules
[ "$($B uname -r)" = 5.15.178-android13-8-00021-g6f2f96be86b9-ab13729987 ] || exit 30
echo STOCK_MODULE_PLAN_BEGIN=wcd938x_slave_dlkm
if $B grep -q '^swr_dlkm ' /proc/modules; then
 echo MODULE_ALREADY_PRESENT=swr_dlkm
else
 echo 'e7a8049b17232cd472ea01b2694d0f65012d08839450bdb537332dd6ff103402  '$M/swr_dlkm.ko | $B sha256sum -c -
 echo MODULE_LOAD_BEGIN=swr_dlkm.ko
 $B timeout 12 $B insmod $M/swr_dlkm.ko || { code=$?; echo MODULE_LOAD_FAILED=swr_dlkm.ko:$code; exit $code; }
 $B grep '^swr_dlkm ' /proc/modules
fi
if $B grep -q '^wcd938x_slave_dlkm ' /proc/modules; then
 echo MODULE_ALREADY_PRESENT=wcd938x_slave_dlkm
else
 echo 'e3e2eb04c3d1d7cc56bcbff97453515eb99f3be9aad34c6ef65b909ce114117c  '$M/wcd938x_slave_dlkm.ko | $B sha256sum -c -
 echo MODULE_LOAD_BEGIN=wcd938x_slave_dlkm.ko
 $B timeout 12 $B insmod $M/wcd938x_slave_dlkm.ko || { code=$?; echo MODULE_LOAD_FAILED=wcd938x_slave_dlkm.ko:$code; exit $code; }
 $B grep '^wcd938x_slave_dlkm ' /proc/modules
fi
echo STOCK_MODULE_PLAN_COMPLETE=wcd938x_slave_dlkm
