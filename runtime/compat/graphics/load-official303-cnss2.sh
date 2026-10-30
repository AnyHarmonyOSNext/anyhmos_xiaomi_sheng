#!/busybox sh
set -eu
B=/busybox
R=/hmos-root
M=$R/vendor_dlkm/lib/modules
[ "$($B uname -r)" = 5.15.178-android13-8-00021-g6f2f96be86b9-ab13729987 ] || exit 30
echo STOCK_MODULE_PLAN_BEGIN=cnss2
if $B grep -q '^qmi_helpers ' /proc/modules; then
 echo MODULE_ALREADY_PRESENT=qmi_helpers
else
 echo '4468511bc7a7f425020a760a841ad3b09159d448aaaa46c3fbf85adcc797a335  '$M/qmi_helpers.ko | $B sha256sum -c -
 echo MODULE_LOAD_BEGIN=qmi_helpers.ko
 $B timeout 12 $B insmod $M/qmi_helpers.ko || { code=$?; echo MODULE_LOAD_FAILED=qmi_helpers.ko:$code; exit $code; }
 $B grep '^qmi_helpers ' /proc/modules
fi
if $B grep -q '^wlan_firmware_service ' /proc/modules; then
 echo MODULE_ALREADY_PRESENT=wlan_firmware_service
else
 echo 'be8b1fce20a872115cbfde7a0651349b9f725983f9288c003547fcf570727885  '$M/wlan_firmware_service.ko | $B sha256sum -c -
 echo MODULE_LOAD_BEGIN=wlan_firmware_service.ko
 $B timeout 12 $B insmod $M/wlan_firmware_service.ko || { code=$?; echo MODULE_LOAD_FAILED=wlan_firmware_service.ko:$code; exit $code; }
 $B grep '^wlan_firmware_service ' /proc/modules
fi
if $B grep -q '^cnss_plat_ipc_qmi_svc ' /proc/modules; then
 echo MODULE_ALREADY_PRESENT=cnss_plat_ipc_qmi_svc
else
 echo 'd1a5c2a8053e20c29d1e2541070a2b153793df048d8af7f871fd4551f29eb243  '$M/cnss_plat_ipc_qmi_svc.ko | $B sha256sum -c -
 echo MODULE_LOAD_BEGIN=cnss_plat_ipc_qmi_svc.ko
 $B timeout 12 $B insmod $M/cnss_plat_ipc_qmi_svc.ko || { code=$?; echo MODULE_LOAD_FAILED=cnss_plat_ipc_qmi_svc.ko:$code; exit $code; }
 $B grep '^cnss_plat_ipc_qmi_svc ' /proc/modules
fi
if $B grep -q '^cnss_utils ' /proc/modules; then
 echo MODULE_ALREADY_PRESENT=cnss_utils
else
 echo 'b6709f66adc36dd2f4816ce93f851558a5f11670f329f83d95e7b13bb4aa21d6  '$M/cnss_utils.ko | $B sha256sum -c -
 echo MODULE_LOAD_BEGIN=cnss_utils.ko
 $B timeout 12 $B insmod $M/cnss_utils.ko || { code=$?; echo MODULE_LOAD_FAILED=cnss_utils.ko:$code; exit $code; }
 $B grep '^cnss_utils ' /proc/modules
fi
if $B grep -q '^qcom_ramdump ' /proc/modules; then
 echo MODULE_ALREADY_PRESENT=qcom_ramdump
else
 echo '4918eb023ee396b9edc05c4cc906e2e688aef4233ee89050ad8ce060702f6ef7  '$M/qcom_ramdump.ko | $B sha256sum -c -
 echo MODULE_LOAD_BEGIN=qcom_ramdump.ko
 $B timeout 12 $B insmod $M/qcom_ramdump.ko || { code=$?; echo MODULE_LOAD_FAILED=qcom_ramdump.ko:$code; exit $code; }
 $B grep '^qcom_ramdump ' /proc/modules
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
if $B grep -q '^cnss2 ' /proc/modules; then
 echo MODULE_ALREADY_PRESENT=cnss2
else
 echo 'fe601aeca4a84e159db57c438bae84a2549203bdb59688c02e9a0f14db06a651  '$M/cnss2.ko | $B sha256sum -c -
 echo MODULE_LOAD_BEGIN=cnss2.ko
 $B timeout 12 $B insmod $M/cnss2.ko || { code=$?; echo MODULE_LOAD_FAILED=cnss2.ko:$code; exit $code; }
 $B grep '^cnss2 ' /proc/modules
fi
echo STOCK_MODULE_PLAN_COMPLETE=cnss2
