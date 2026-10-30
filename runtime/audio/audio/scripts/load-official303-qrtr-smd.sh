#!/busybox sh
set -eu
B=/busybox
R=/hmos-root
M=$R/vendor_dlkm/lib/modules
[ "$($B uname -r)" = 5.15.178-android13-8-00021-g6f2f96be86b9-ab13729987 ] || exit 30
echo STOCK_MODULE_PLAN_BEGIN=qrtr-smd
if $B grep -q '^qcom_glink ' /proc/modules; then
 echo MODULE_ALREADY_PRESENT=qcom_glink
else
 echo '03e82a8bd2757bb5cf776ac00e3aa596d67d063885ee1dcc931cb2dd0dc56f9b  '$M/qcom_glink.ko | $B sha256sum -c -
 echo MODULE_LOAD_BEGIN=qcom_glink.ko
 $B timeout 12 $B insmod $M/qcom_glink.ko || { code=$?; echo MODULE_LOAD_FAILED=qcom_glink.ko:$code; exit $code; }
 $B grep '^qcom_glink ' /proc/modules
fi
if $B grep -q '^qrtr_smd ' /proc/modules; then
 echo MODULE_ALREADY_PRESENT=qrtr_smd
else
 echo 'ce66b2655fd7d3d9414f552c977161b9a613a6477dad7c063c7ec9f8e02bc5a7  '$M/qrtr-smd.ko | $B sha256sum -c -
 echo MODULE_LOAD_BEGIN=qrtr-smd.ko
 $B timeout 12 $B insmod $M/qrtr-smd.ko || { code=$?; echo MODULE_LOAD_FAILED=qrtr-smd.ko:$code; exit $code; }
 $B grep '^qrtr_smd ' /proc/modules
fi
echo STOCK_MODULE_PLAN_COMPLETE=qrtr-smd
