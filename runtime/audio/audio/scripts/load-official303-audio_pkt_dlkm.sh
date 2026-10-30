#!/busybox sh
set -eu
B=/busybox
R=/hmos-root
M=$R/vendor_dlkm/lib/modules
[ "$($B uname -r)" = 5.15.178-android13-8-00021-g6f2f96be86b9-ab13729987 ] || exit 30
echo STOCK_MODULE_PLAN_BEGIN=audio_pkt_dlkm
if $B grep -q '^audpkt_ion_dlkm ' /proc/modules; then
 echo MODULE_ALREADY_PRESENT=audpkt_ion_dlkm
else
 echo 'b95ac3a195c0f3a0cac800b9e68c50bcb1591c9c4a5e7ca0ba98604b99311894  '$M/audpkt_ion_dlkm.ko | $B sha256sum -c -
 echo MODULE_LOAD_BEGIN=audpkt_ion_dlkm.ko
 $B timeout 12 $B insmod $M/audpkt_ion_dlkm.ko || { code=$?; echo MODULE_LOAD_FAILED=audpkt_ion_dlkm.ko:$code; exit $code; }
 $B grep '^audpkt_ion_dlkm ' /proc/modules
fi
if $B grep -q '^snd_event_dlkm ' /proc/modules; then
 echo MODULE_ALREADY_PRESENT=snd_event_dlkm
else
 echo '101de1cc66b5076cae0e3ec0f33dbf928d0ef9ee17492e22fdbbf9efb17eda38  '$M/snd_event_dlkm.ko | $B sha256sum -c -
 echo MODULE_LOAD_BEGIN=snd_event_dlkm.ko
 $B timeout 12 $B insmod $M/snd_event_dlkm.ko || { code=$?; echo MODULE_LOAD_FAILED=snd_event_dlkm.ko:$code; exit $code; }
 $B grep '^snd_event_dlkm ' /proc/modules
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
if $B grep -q '^q6_pdr_dlkm ' /proc/modules; then
 echo MODULE_ALREADY_PRESENT=q6_pdr_dlkm
else
 echo '5d9592b08cb560c07e1b8b7140abbe1630e9b7c237422bc4bb0f285b4a028bfb  '$M/q6_pdr_dlkm.ko | $B sha256sum -c -
 echo MODULE_LOAD_BEGIN=q6_pdr_dlkm.ko
 $B timeout 12 $B insmod $M/q6_pdr_dlkm.ko || { code=$?; echo MODULE_LOAD_FAILED=q6_pdr_dlkm.ko:$code; exit $code; }
 $B grep '^q6_pdr_dlkm ' /proc/modules
fi
if $B grep -q '^q6_notifier_dlkm ' /proc/modules; then
 echo MODULE_ALREADY_PRESENT=q6_notifier_dlkm
else
 echo '2f23c7594241b845f41b49d6a638af298245dd19f8374118f0334a9c401677dc  '$M/q6_notifier_dlkm.ko | $B sha256sum -c -
 echo MODULE_LOAD_BEGIN=q6_notifier_dlkm.ko
 $B timeout 12 $B insmod $M/q6_notifier_dlkm.ko || { code=$?; echo MODULE_LOAD_FAILED=q6_notifier_dlkm.ko:$code; exit $code; }
 $B grep '^q6_notifier_dlkm ' /proc/modules
fi
if $B grep -q '^gpr_dlkm ' /proc/modules; then
 echo MODULE_ALREADY_PRESENT=gpr_dlkm
else
 echo 'f434721b398ad697d3874424d1634c6d220c920b229668d8e7e8619f572350a5  '$M/gpr_dlkm.ko | $B sha256sum -c -
 echo MODULE_LOAD_BEGIN=gpr_dlkm.ko
 $B timeout 12 $B insmod $M/gpr_dlkm.ko || { code=$?; echo MODULE_LOAD_FAILED=gpr_dlkm.ko:$code; exit $code; }
 $B grep '^gpr_dlkm ' /proc/modules
fi
if $B grep -q '^spf_core_dlkm ' /proc/modules; then
 echo MODULE_ALREADY_PRESENT=spf_core_dlkm
else
 echo '2e22232b89832c91700ac692543cf7dea602493429a0e888e8bc6856a552d116  '$M/spf_core_dlkm.ko | $B sha256sum -c -
 echo MODULE_LOAD_BEGIN=spf_core_dlkm.ko
 $B timeout 12 $B insmod $M/spf_core_dlkm.ko || { code=$?; echo MODULE_LOAD_FAILED=spf_core_dlkm.ko:$code; exit $code; }
 $B grep '^spf_core_dlkm ' /proc/modules
fi
if $B grep -q '^audio_pkt_dlkm ' /proc/modules; then
 echo MODULE_ALREADY_PRESENT=audio_pkt_dlkm
else
 echo '950f5dd769bb464b13b9bee7036eaa338003cc79ffddb039c7987da8b8153178  '$M/audio_pkt_dlkm.ko | $B sha256sum -c -
 echo MODULE_LOAD_BEGIN=audio_pkt_dlkm.ko
 $B timeout 12 $B insmod $M/audio_pkt_dlkm.ko || { code=$?; echo MODULE_LOAD_FAILED=audio_pkt_dlkm.ko:$code; exit $code; }
 $B grep '^audio_pkt_dlkm ' /proc/modules
fi
echo STOCK_MODULE_PLAN_COMPLETE=audio_pkt_dlkm
