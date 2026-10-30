#!/busybox sh
set -eu
B=/busybox
R=/hmos-root
M=$R/vendor_dlkm/lib/modules
[ "$($B uname -r)" = 5.15.178-android13-8-00021-g6f2f96be86b9-ab13729987 ] || exit 30
echo AUDIO_TRANSPORT_BEGIN=1
if ! $B grep -q '^xlogchar ' /proc/modules; then
 echo 'f5380818c09e6487064bf6530c663199d4cbabb566a817062f6b06e59bb47dfd  '$M/xlogchar.ko | $B sha256sum -c -
 echo AUDIO_MODULE_BEGIN=xlogchar.ko
 $B timeout 12 $B insmod $M/xlogchar.ko
 $B grep '^xlogchar ' /proc/modules
fi
if ! $B grep -q '^snd_event_dlkm ' /proc/modules; then
 echo '101de1cc66b5076cae0e3ec0f33dbf928d0ef9ee17492e22fdbbf9efb17eda38  '$M/snd_event_dlkm.ko | $B sha256sum -c -
 echo AUDIO_MODULE_BEGIN=snd_event_dlkm.ko
 $B timeout 12 $B insmod $M/snd_event_dlkm.ko
 $B grep '^snd_event_dlkm ' /proc/modules
fi
if ! $B grep -q '^qcom_smd ' /proc/modules; then
 echo 'f80df64fb8f265c5f3b3a2e5c58c0de9c42ae66a9bf1748c1488c18adce94733  '$M/qcom_smd.ko | $B sha256sum -c -
 echo AUDIO_MODULE_BEGIN=qcom_smd.ko
 $B timeout 12 $B insmod $M/qcom_smd.ko
 $B grep '^qcom_smd ' /proc/modules
fi
if ! $B grep -q '^qcom_glink ' /proc/modules; then
 echo '03e82a8bd2757bb5cf776ac00e3aa596d67d063885ee1dcc931cb2dd0dc56f9b  '$M/qcom_glink.ko | $B sha256sum -c -
 echo AUDIO_MODULE_BEGIN=qcom_glink.ko
 $B timeout 12 $B insmod $M/qcom_glink.ko
 $B grep '^qcom_glink ' /proc/modules
fi
if ! $B grep -q '^qcom_glink_smem ' /proc/modules; then
 echo '6e400a1bff0f52ac14080ddc663634719a624a28a35cb025d09d3eee2e142449  '$M/qcom_glink_smem.ko | $B sha256sum -c -
 echo AUDIO_MODULE_BEGIN=qcom_glink_smem.ko
 $B timeout 12 $B insmod $M/qcom_glink_smem.ko
 $B grep '^qcom_glink_smem ' /proc/modules
fi
if ! $B grep -q '^rproc_qcom_common ' /proc/modules; then
 echo '3f6d255301e9eb4f6c3bbe50d09fb1eb04df644b027b32847bbedf72fc12c75e  '$M/rproc_qcom_common.ko | $B sha256sum -c -
 echo AUDIO_MODULE_BEGIN=rproc_qcom_common.ko
 $B timeout 12 $B insmod $M/rproc_qcom_common.ko
 $B grep '^rproc_qcom_common ' /proc/modules
fi
if ! $B grep -q '^qmi_helpers ' /proc/modules; then
 echo '4468511bc7a7f425020a760a841ad3b09159d448aaaa46c3fbf85adcc797a335  '$M/qmi_helpers.ko | $B sha256sum -c -
 echo AUDIO_MODULE_BEGIN=qmi_helpers.ko
 $B timeout 12 $B insmod $M/qmi_helpers.ko
 $B grep '^qmi_helpers ' /proc/modules
fi
if ! $B grep -q '^pdr_interface ' /proc/modules; then
 echo 'b3a519cfbce7c4363c8f372e5dde583e2ea81f0aea4ba312fe7f5ae696190d88  '$M/pdr_interface.ko | $B sha256sum -c -
 echo AUDIO_MODULE_BEGIN=pdr_interface.ko
 $B timeout 12 $B insmod $M/pdr_interface.ko
 $B grep '^pdr_interface ' /proc/modules
fi
if ! $B grep -q '^q6_pdr_dlkm ' /proc/modules; then
 echo '5d9592b08cb560c07e1b8b7140abbe1630e9b7c237422bc4bb0f285b4a028bfb  '$M/q6_pdr_dlkm.ko | $B sha256sum -c -
 echo AUDIO_MODULE_BEGIN=q6_pdr_dlkm.ko
 $B timeout 12 $B insmod $M/q6_pdr_dlkm.ko
 $B grep '^q6_pdr_dlkm ' /proc/modules
fi
if ! $B grep -q '^q6_notifier_dlkm ' /proc/modules; then
 echo '2f23c7594241b845f41b49d6a638af298245dd19f8374118f0334a9c401677dc  '$M/q6_notifier_dlkm.ko | $B sha256sum -c -
 echo AUDIO_MODULE_BEGIN=q6_notifier_dlkm.ko
 $B timeout 12 $B insmod $M/q6_notifier_dlkm.ko
 $B grep '^q6_notifier_dlkm ' /proc/modules
fi
if ! $B grep -q '^gpr_dlkm ' /proc/modules; then
 echo 'f434721b398ad697d3874424d1634c6d220c920b229668d8e7e8619f572350a5  '$M/gpr_dlkm.ko | $B sha256sum -c -
 echo AUDIO_MODULE_BEGIN=gpr_dlkm.ko
 $B timeout 12 $B insmod $M/gpr_dlkm.ko
 $B grep '^gpr_dlkm ' /proc/modules
fi
if ! $B grep -q '^spf_core_dlkm ' /proc/modules; then
 echo '2e22232b89832c91700ac692543cf7dea602493429a0e888e8bc6856a552d116  '$M/spf_core_dlkm.ko | $B sha256sum -c -
 echo AUDIO_MODULE_BEGIN=spf_core_dlkm.ko
 $B timeout 12 $B insmod $M/spf_core_dlkm.ko
 $B grep '^spf_core_dlkm ' /proc/modules
fi
if ! $B grep -q '^adsp_loader_dlkm ' /proc/modules; then
 echo '1c58f68c008a28e4e393febc6f8b7c9e91bf14f4a219ee1340c7deb814ad7220  '$M/adsp_loader_dlkm.ko | $B sha256sum -c -
 echo AUDIO_MODULE_BEGIN=adsp_loader_dlkm.ko
 $B timeout 12 $B insmod $M/adsp_loader_dlkm.ko
 $B grep '^adsp_loader_dlkm ' /proc/modules
fi
if ! $B grep -q '^q6_dlkm ' /proc/modules; then
 echo '6b77ec8e1d97378fc641116d27d091cbe6e05d128a3028b04e126929aeab1159  '$M/q6_dlkm.ko | $B sha256sum -c -
 echo AUDIO_MODULE_BEGIN=q6_dlkm.ko
 $B timeout 12 $B insmod $M/q6_dlkm.ko
 $B grep '^q6_dlkm ' /proc/modules
fi
echo AUDIO_TRANSPORT_COMPLETE=1
