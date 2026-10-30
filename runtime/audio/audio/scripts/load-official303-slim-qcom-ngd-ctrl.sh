#!/busybox sh
set -eu
B=/busybox
R=/hmos-root
M=$R/vendor_dlkm/lib/modules
[ "$($B uname -r)" = 5.15.178-android13-8-00021-g6f2f96be86b9-ab13729987 ] || exit 30
echo STOCK_MODULE_PLAN_BEGIN=slim-qcom-ngd-ctrl
if $B grep -q '^slimbus ' /proc/modules; then
 echo MODULE_ALREADY_PRESENT=slimbus
else
 echo 'add1d3ffb8367d6511eeb4a52cf6b4543d119b1b1182475b4c5fbb4993afcf9e  '$M/slimbus.ko | $B sha256sum -c -
 echo MODULE_LOAD_BEGIN=slimbus.ko
 $B timeout 12 $B insmod $M/slimbus.ko || { code=$?; echo MODULE_LOAD_FAILED=slimbus.ko:$code; exit $code; }
 $B grep '^slimbus ' /proc/modules
fi
if $B grep -q '^qcom_smd ' /proc/modules; then
 echo MODULE_ALREADY_PRESENT=qcom_smd
else
 echo 'f80df64fb8f265c5f3b3a2e5c58c0de9c42ae66a9bf1748c1488c18adce94733  '$M/qcom_smd.ko | $B sha256sum -c -
 echo MODULE_LOAD_BEGIN=qcom_smd.ko
 $B timeout 12 $B insmod $M/qcom_smd.ko || { code=$?; echo MODULE_LOAD_FAILED=qcom_smd.ko:$code; exit $code; }
 $B grep '^qcom_smd ' /proc/modules
fi
if $B grep -q '^qcom_glink ' /proc/modules; then
 echo MODULE_ALREADY_PRESENT=qcom_glink
else
 echo '03e82a8bd2757bb5cf776ac00e3aa596d67d063885ee1dcc931cb2dd0dc56f9b  '$M/qcom_glink.ko | $B sha256sum -c -
 echo MODULE_LOAD_BEGIN=qcom_glink.ko
 $B timeout 12 $B insmod $M/qcom_glink.ko || { code=$?; echo MODULE_LOAD_FAILED=qcom_glink.ko:$code; exit $code; }
 $B grep '^qcom_glink ' /proc/modules
fi
if $B grep -q '^qcom_glink_smem ' /proc/modules; then
 echo MODULE_ALREADY_PRESENT=qcom_glink_smem
else
 echo '6e400a1bff0f52ac14080ddc663634719a624a28a35cb025d09d3eee2e142449  '$M/qcom_glink_smem.ko | $B sha256sum -c -
 echo MODULE_LOAD_BEGIN=qcom_glink_smem.ko
 $B timeout 12 $B insmod $M/qcom_glink_smem.ko || { code=$?; echo MODULE_LOAD_FAILED=qcom_glink_smem.ko:$code; exit $code; }
 $B grep '^qcom_glink_smem ' /proc/modules
fi
if $B grep -q '^rproc_qcom_common ' /proc/modules; then
 echo MODULE_ALREADY_PRESENT=rproc_qcom_common
else
 echo '3f6d255301e9eb4f6c3bbe50d09fb1eb04df644b027b32847bbedf72fc12c75e  '$M/rproc_qcom_common.ko | $B sha256sum -c -
 echo MODULE_LOAD_BEGIN=rproc_qcom_common.ko
 $B timeout 12 $B insmod $M/rproc_qcom_common.ko || { code=$?; echo MODULE_LOAD_FAILED=rproc_qcom_common.ko:$code; exit $code; }
 $B grep '^rproc_qcom_common ' /proc/modules
fi
if $B grep -q '^qmi_helpers ' /proc/modules; then
 echo MODULE_ALREADY_PRESENT=qmi_helpers
else
 echo '4468511bc7a7f425020a760a841ad3b09159d448aaaa46c3fbf85adcc797a335  '$M/qmi_helpers.ko | $B sha256sum -c -
 echo MODULE_LOAD_BEGIN=qmi_helpers.ko
 $B timeout 12 $B insmod $M/qmi_helpers.ko || { code=$?; echo MODULE_LOAD_FAILED=qmi_helpers.ko:$code; exit $code; }
 $B grep '^qmi_helpers ' /proc/modules
fi
if $B grep -q '^pdr_interface ' /proc/modules; then
 echo MODULE_ALREADY_PRESENT=pdr_interface
else
 echo 'b3a519cfbce7c4363c8f372e5dde583e2ea81f0aea4ba312fe7f5ae696190d88  '$M/pdr_interface.ko | $B sha256sum -c -
 echo MODULE_LOAD_BEGIN=pdr_interface.ko
 $B timeout 12 $B insmod $M/pdr_interface.ko || { code=$?; echo MODULE_LOAD_FAILED=pdr_interface.ko:$code; exit $code; }
 $B grep '^pdr_interface ' /proc/modules
fi
if $B grep -q '^slim_qcom_ngd_ctrl ' /proc/modules; then
 echo MODULE_ALREADY_PRESENT=slim_qcom_ngd_ctrl
else
 echo '3cfd6fdc0d0a8faf2a81208eed6eaae717cb59227dc05a884420d0e87a3369d7  '$M/slim-qcom-ngd-ctrl.ko | $B sha256sum -c -
 echo MODULE_LOAD_BEGIN=slim-qcom-ngd-ctrl.ko
 $B timeout 12 $B insmod $M/slim-qcom-ngd-ctrl.ko || { code=$?; echo MODULE_LOAD_FAILED=slim-qcom-ngd-ctrl.ko:$code; exit $code; }
 $B grep '^slim_qcom_ngd_ctrl ' /proc/modules
fi
echo STOCK_MODULE_PLAN_COMPLETE=slim-qcom-ngd-ctrl
