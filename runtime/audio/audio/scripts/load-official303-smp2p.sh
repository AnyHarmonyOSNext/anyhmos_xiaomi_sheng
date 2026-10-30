#!/busybox sh
set -eu
B=/busybox
R=/hmos-root
M=$R/vendor_dlkm/lib/modules
[ "$($B uname -r)" = 5.15.178-android13-8-00021-g6f2f96be86b9-ab13729987 ] || exit 30
echo STOCK_MODULE_PLAN_BEGIN=smp2p
if $B grep -q '^smp2p ' /proc/modules; then
 echo MODULE_ALREADY_PRESENT=smp2p
else
 echo '73fa6f28e075b4546ec07e24002a550b51ef0679a63002e305727f861df8a7d5  '$M/smp2p.ko | $B sha256sum -c -
 echo MODULE_LOAD_BEGIN=smp2p.ko
 $B timeout 12 $B insmod $M/smp2p.ko || { code=$?; echo MODULE_LOAD_FAILED=smp2p.ko:$code; exit $code; }
 $B grep '^smp2p ' /proc/modules
fi
echo STOCK_MODULE_PLAN_COMPLETE=smp2p
