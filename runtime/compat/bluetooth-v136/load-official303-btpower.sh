#!/busybox sh
set -eu
B=/busybox
R=/hmos-root
M=$R/vendor_dlkm/lib/modules
[ "$($B uname -r)" = 5.15.178-android13-8-00021-g6f2f96be86b9-ab13729987 ] || exit 30
echo STOCK_MODULE_PLAN_BEGIN=btpower
if $B grep -q '^cnss_utils ' /proc/modules; then
 echo MODULE_ALREADY_PRESENT=cnss_utils
else
 echo 'b6709f66adc36dd2f4816ce93f851558a5f11670f329f83d95e7b13bb4aa21d6  '$M/cnss_utils.ko | $B sha256sum -c -
 echo MODULE_LOAD_BEGIN=cnss_utils.ko
 $B timeout 12 $B insmod $M/cnss_utils.ko || { code=$?; echo MODULE_LOAD_FAILED=cnss_utils.ko:$code; exit $code; }
 $B grep '^cnss_utils ' /proc/modules
fi
if $B grep -q '^qseecom_proxy ' /proc/modules; then
 echo MODULE_ALREADY_PRESENT=qseecom_proxy
else
 echo '31a8a8c2a50c75e060106be992d7349bcba795bba23cc5a387eb975617f14048  '$M/qseecom_proxy.ko | $B sha256sum -c -
 echo MODULE_LOAD_BEGIN=qseecom_proxy.ko
 $B timeout 12 $B insmod $M/qseecom_proxy.ko || { code=$?; echo MODULE_LOAD_FAILED=qseecom_proxy.ko:$code; exit $code; }
 $B grep '^qseecom_proxy ' /proc/modules
fi
if $B grep -q '^smcinvoke_dlkm ' /proc/modules; then
 echo MODULE_ALREADY_PRESENT=smcinvoke_dlkm
else
 echo '59d3d220f2dbe4b07b51707c45c7f3d5f08039ce2a917d526b2e22633b21441b  '$M/smcinvoke_dlkm.ko | $B sha256sum -c -
 echo MODULE_LOAD_BEGIN=smcinvoke_dlkm.ko
 $B timeout 12 $B insmod $M/smcinvoke_dlkm.ko || { code=$?; echo MODULE_LOAD_FAILED=smcinvoke_dlkm.ko:$code; exit $code; }
 $B grep '^smcinvoke_dlkm ' /proc/modules
fi
if $B grep -q '^btpower ' /proc/modules; then
 echo MODULE_ALREADY_PRESENT=btpower
else
 echo '09940dacfa67420601f5130676b82dc5d6ea393cf90c7b4154299dc9d92087e2  '$M/btpower.ko | $B sha256sum -c -
 echo MODULE_LOAD_BEGIN=btpower.ko
 $B timeout 12 $B insmod $M/btpower.ko || { code=$?; echo MODULE_LOAD_FAILED=btpower.ko:$code; exit $code; }
 $B grep '^btpower ' /proc/modules
fi
echo STOCK_MODULE_PLAN_COMPLETE=btpower
