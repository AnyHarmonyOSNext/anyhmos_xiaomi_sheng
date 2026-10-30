#!/busybox sh
set -eu
B=/busybox
R=/hmos-root
M=$R/vendor_dlkm/lib/modules
[ "$($B uname -r)" = 5.15.178-android13-8-00021-g6f2f96be86b9-ab13729987 ] || exit 30
echo STOCK_MODULE_PLAN_BEGIN=qcom_q6v5_pas
if $B grep -q '^qcom_pil_info ' /proc/modules; then
 echo MODULE_ALREADY_PRESENT=qcom_pil_info
else
 echo 'bb8a61ad86de07b92bb6594cb8106893145ff1927f0315b5cbdf6b8461f34ce0  '$M/qcom_pil_info.ko | $B sha256sum -c -
 echo MODULE_LOAD_BEGIN=qcom_pil_info.ko
 $B timeout 12 $B insmod $M/qcom_pil_info.ko || { code=$?; echo MODULE_LOAD_FAILED=qcom_pil_info.ko:$code; exit $code; }
 $B grep '^qcom_pil_info ' /proc/modules
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
if $B grep -q '^qcom_sysmon ' /proc/modules; then
 echo MODULE_ALREADY_PRESENT=qcom_sysmon
else
 echo '027fa2b395f4b6adf08e0caf19021147f430a765571ed02b507430a847bdfcf3  '$M/qcom_sysmon.ko | $B sha256sum -c -
 echo MODULE_LOAD_BEGIN=qcom_sysmon.ko
 $B timeout 12 $B insmod $M/qcom_sysmon.ko || { code=$?; echo MODULE_LOAD_FAILED=qcom_sysmon.ko:$code; exit $code; }
 $B grep '^qcom_sysmon ' /proc/modules
fi
if $B grep -q '^qcom_q6v5 ' /proc/modules; then
 echo MODULE_ALREADY_PRESENT=qcom_q6v5
else
 echo '1da2f28ab57a8475f513bd76fa664cfb093d40511a9edfeb2f7429fa2aeea0d7  '$M/qcom_q6v5.ko | $B sha256sum -c -
 echo MODULE_LOAD_BEGIN=qcom_q6v5.ko
 $B timeout 12 $B insmod $M/qcom_q6v5.ko || { code=$?; echo MODULE_LOAD_FAILED=qcom_q6v5.ko:$code; exit $code; }
 $B grep '^qcom_q6v5 ' /proc/modules
fi
if $B grep -q '^qcom_ramdump ' /proc/modules; then
 echo MODULE_ALREADY_PRESENT=qcom_ramdump
else
 echo '4918eb023ee396b9edc05c4cc906e2e688aef4233ee89050ad8ce060702f6ef7  '$M/qcom_ramdump.ko | $B sha256sum -c -
 echo MODULE_LOAD_BEGIN=qcom_ramdump.ko
 $B timeout 12 $B insmod $M/qcom_ramdump.ko || { code=$?; echo MODULE_LOAD_FAILED=qcom_ramdump.ko:$code; exit $code; }
 $B grep '^qcom_ramdump ' /proc/modules
fi
if $B grep -q '^qcom_q6v5_pas ' /proc/modules; then
 echo MODULE_ALREADY_PRESENT=qcom_q6v5_pas
else
 echo '163181f64268ef11028bf92df22dcec46e573f7824685fadc5013868d0e96a5f  '$M/qcom_q6v5_pas.ko | $B sha256sum -c -
 echo MODULE_LOAD_BEGIN=qcom_q6v5_pas.ko
 $B timeout 12 $B insmod $M/qcom_q6v5_pas.ko || { code=$?; echo MODULE_LOAD_FAILED=qcom_q6v5_pas.ko:$code; exit $code; }
 $B grep '^qcom_q6v5_pas ' /proc/modules
fi
echo STOCK_MODULE_PLAN_COMPLETE=qcom_q6v5_pas
