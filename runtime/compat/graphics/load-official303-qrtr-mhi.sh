#!/busybox sh
set -eu
B=/busybox
R=/hmos-root
M=$R/vendor_dlkm/lib/modules
[ "$($B uname -r)" = 5.15.178-android13-8-00021-g6f2f96be86b9-ab13729987 ] || exit 30
echo STOCK_MODULE_PLAN_BEGIN=qrtr-mhi
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
if $B grep -q '^pci_msm_drv ' /proc/modules; then
 echo MODULE_ALREADY_PRESENT=pci_msm_drv
else
 echo '973768ce442779a73b9e05c68e0159e896bd807dc62a1bba36839583a8e310f0  '$M/pci-msm-drv.ko | $B sha256sum -c -
 echo MODULE_LOAD_BEGIN=pci-msm-drv.ko
 $B timeout 12 $B insmod $M/pci-msm-drv.ko || { code=$?; echo MODULE_LOAD_FAILED=pci-msm-drv.ko:$code; exit $code; }
 $B grep '^pci_msm_drv ' /proc/modules
fi
if $B grep -q '^mhi ' /proc/modules; then
 echo MODULE_ALREADY_PRESENT=mhi
else
 echo '9cbe0bd6dc01825a7f85ca88d860754362eaff97825caa999b2b6a1631d55173  '$M/mhi.ko | $B sha256sum -c -
 echo MODULE_LOAD_BEGIN=mhi.ko
 $B timeout 12 $B insmod $M/mhi.ko || { code=$?; echo MODULE_LOAD_FAILED=mhi.ko:$code; exit $code; }
 $B grep '^mhi ' /proc/modules
fi
if $B grep -q '^qrtr_mhi ' /proc/modules; then
 echo MODULE_ALREADY_PRESENT=qrtr_mhi
else
 echo '6cf58f4fbac95d152b87e85c6c070cd8268b9b2e5ded4ace10f51016593146eb  '$M/qrtr-mhi.ko | $B sha256sum -c -
 echo MODULE_LOAD_BEGIN=qrtr-mhi.ko
 $B timeout 12 $B insmod $M/qrtr-mhi.ko || { code=$?; echo MODULE_LOAD_FAILED=qrtr-mhi.ko:$code; exit $code; }
 $B grep '^qrtr_mhi ' /proc/modules
fi
echo STOCK_MODULE_PLAN_COMPLETE=qrtr-mhi
