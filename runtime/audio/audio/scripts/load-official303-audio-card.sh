#!/busybox sh
set -eu
B=/busybox
R=/hmos-root
M=$R/vendor_dlkm/lib/modules
[ "$($B uname -r)" = 5.15.178-android13-8-00021-g6f2f96be86b9-ab13729987 ] || exit 30
echo AUDIO_CARD_BEGIN=1
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
if ! $B grep -q '^pinctrl_lpi_dlkm ' /proc/modules; then
 echo 'c8402aaa70691b4bf1ccf73bea92e26dbd7c153bc905f57fc6c9826bd9f3b5b5  '$M/pinctrl_lpi_dlkm.ko | $B sha256sum -c -
 echo AUDIO_MODULE_BEGIN=pinctrl_lpi_dlkm.ko
 $B timeout 12 $B insmod $M/pinctrl_lpi_dlkm.ko
 $B grep '^pinctrl_lpi_dlkm ' /proc/modules
fi
if ! $B grep -q '^stub_dlkm ' /proc/modules; then
 echo 'fac3f65dd6e663296df3c1ebca3ad350b8702fc97c653d618bf097d4107b0d9d  '$M/stub_dlkm.ko | $B sha256sum -c -
 echo AUDIO_MODULE_BEGIN=stub_dlkm.ko
 $B timeout 12 $B insmod $M/stub_dlkm.ko
 $B grep '^stub_dlkm ' /proc/modules
fi
if ! $B grep -q '^swr_dlkm ' /proc/modules; then
 echo 'e7a8049b17232cd472ea01b2694d0f65012d08839450bdb537332dd6ff103402  '$M/swr_dlkm.ko | $B sha256sum -c -
 echo AUDIO_MODULE_BEGIN=swr_dlkm.ko
 $B timeout 12 $B insmod $M/swr_dlkm.ko
 $B grep '^swr_dlkm ' /proc/modules
fi
if ! $B grep -q '^swr_ctrl_dlkm ' /proc/modules; then
 echo '40fd93955c17b5870bf89b44932905ee32c31a6a0ac79b6ebf09a5ec1f36ea8a  '$M/swr_ctrl_dlkm.ko | $B sha256sum -c -
 echo AUDIO_MODULE_BEGIN=swr_ctrl_dlkm.ko
 $B timeout 12 $B insmod $M/swr_ctrl_dlkm.ko
 $B grep '^swr_ctrl_dlkm ' /proc/modules
fi
if ! $B grep -q '^wcd_core_dlkm ' /proc/modules; then
 echo 'd8bc3cf5d808b63e97f5892c35aaa7866f94e047c3774194552dba718b21384f  '$M/wcd_core_dlkm.ko | $B sha256sum -c -
 echo AUDIO_MODULE_BEGIN=wcd_core_dlkm.ko
 $B timeout 12 $B insmod $M/wcd_core_dlkm.ko
 $B grep '^wcd_core_dlkm ' /proc/modules
fi
if ! $B grep -q '^lpass_cdc_dlkm ' /proc/modules; then
 echo '7c8bf44a7bde359f2fdceaa96220fce041b7cb025bcd1c49095d2feec5ae706a  '$M/lpass_cdc_dlkm.ko | $B sha256sum -c -
 echo AUDIO_MODULE_BEGIN=lpass_cdc_dlkm.ko
 $B timeout 12 $B insmod $M/lpass_cdc_dlkm.ko
 $B grep '^lpass_cdc_dlkm ' /proc/modules
fi
if ! $B grep -q '^lpass_cdc_va_macro_dlkm ' /proc/modules; then
 echo 'f37483d9ab3d2e42d28c4e173d928544798648383e1ee6fce79f40d93ba7be5b  '$M/lpass_cdc_va_macro_dlkm.ko | $B sha256sum -c -
 echo AUDIO_MODULE_BEGIN=lpass_cdc_va_macro_dlkm.ko
 $B timeout 12 $B insmod $M/lpass_cdc_va_macro_dlkm.ko
 $B grep '^lpass_cdc_va_macro_dlkm ' /proc/modules
fi
if ! $B grep -q '^lpass_cdc_wsa_macro_dlkm ' /proc/modules; then
 echo '9f6b81fb4b5b98d1dcd5ec847ded22a9566a6e33591b58672db633d0dd23796f  '$M/lpass_cdc_wsa_macro_dlkm.ko | $B sha256sum -c -
 echo AUDIO_MODULE_BEGIN=lpass_cdc_wsa_macro_dlkm.ko
 $B timeout 12 $B insmod $M/lpass_cdc_wsa_macro_dlkm.ko
 $B grep '^lpass_cdc_wsa_macro_dlkm ' /proc/modules
fi
if ! $B grep -q '^lpass_cdc_wsa2_macro_dlkm ' /proc/modules; then
 echo '4dd8e4fc208f92f89b7cee957b4b2f000c6314c37a198f377026115df0d8bc57  '$M/lpass_cdc_wsa2_macro_dlkm.ko | $B sha256sum -c -
 echo AUDIO_MODULE_BEGIN=lpass_cdc_wsa2_macro_dlkm.ko
 $B timeout 12 $B insmod $M/lpass_cdc_wsa2_macro_dlkm.ko
 $B grep '^lpass_cdc_wsa2_macro_dlkm ' /proc/modules
fi
if ! $B grep -q '^xm_utils ' /proc/modules; then
 echo 'f5b062a2a9afddb1e9cbe01836d3778a22bfd1c22a23be35d89f2cf2985d556d  '$M/xm_utils.ko | $B sha256sum -c -
 echo AUDIO_MODULE_BEGIN=xm_utils.ko
 $B timeout 12 $B insmod $M/xm_utils.ko
 $B grep '^xm_utils ' /proc/modules
fi
if ! $B grep -q '^pmic_glink ' /proc/modules; then
 echo 'f21eeb219ced392e81f46b600242dcd597c4b7d21a0c589b7fa286c55efb7c76  '$M/pmic_glink.ko | $B sha256sum -c -
 echo AUDIO_MODULE_BEGIN=pmic_glink.ko
 $B timeout 12 $B insmod $M/pmic_glink.ko
 $B grep '^pmic_glink ' /proc/modules
fi
if ! $B grep -q '^panel_event_notifier ' /proc/modules; then
 echo 'eaa8c847c5341f570edc5592189b4b8715e7fb95f26f8ce9c07e7bfe1a0575be  '$M/panel_event_notifier.ko | $B sha256sum -c -
 echo AUDIO_MODULE_BEGIN=panel_event_notifier.ko
 $B timeout 12 $B insmod $M/panel_event_notifier.ko
 $B grep '^panel_event_notifier ' /proc/modules
fi
if ! $B grep -q '^qti_battery_charger ' /proc/modules; then
 echo '3190a88b2bbc3abb3de123a08233c0ebea2bade2e424d67f18e62ea9e2e38047  '$M/qti_battery_charger.ko | $B sha256sum -c -
 echo AUDIO_MODULE_BEGIN=qti_battery_charger.ko
 $B timeout 12 $B insmod $M/qti_battery_charger.ko
 $B grep '^qti_battery_charger ' /proc/modules
fi
if ! $B grep -q '^swr_haptics_dlkm ' /proc/modules; then
 echo '7ccc80a3e891acadfd0f17cec7aa80aeef468780f23628640777f827faa233d2  '$M/swr_haptics_dlkm.ko | $B sha256sum -c -
 echo AUDIO_MODULE_BEGIN=swr_haptics_dlkm.ko
 $B timeout 12 $B insmod $M/swr_haptics_dlkm.ko
 $B grep '^swr_haptics_dlkm ' /proc/modules
fi
if ! $B grep -q '^msm_ext_display ' /proc/modules; then
 echo '6ee19dfb94e49b2c3605b03a62ba4327a7198627874501a2c124db7e670341d2  '$M/msm_ext_display.ko | $B sha256sum -c -
 echo AUDIO_MODULE_BEGIN=msm_ext_display.ko
 $B timeout 12 $B insmod $M/msm_ext_display.ko
 $B grep '^msm_ext_display ' /proc/modules
fi
if ! $B grep -q '^hdmi_dlkm ' /proc/modules; then
 echo 'e0b1120adaa0157defeb3eefadde79c912309a5769e6cd6a678770cbe7be5875  '$M/hdmi_dlkm.ko | $B sha256sum -c -
 echo AUDIO_MODULE_BEGIN=hdmi_dlkm.ko
 $B timeout 12 $B insmod $M/hdmi_dlkm.ko
 $B grep '^hdmi_dlkm ' /proc/modules
fi
if ! $B grep -q '^xlogchar ' /proc/modules; then
 echo 'f5380818c09e6487064bf6530c663199d4cbabb566a817062f6b06e59bb47dfd  '$M/xlogchar.ko | $B sha256sum -c -
 echo AUDIO_MODULE_BEGIN=xlogchar.ko
 $B timeout 12 $B insmod $M/xlogchar.ko
 $B grep '^xlogchar ' /proc/modules
fi
if ! $B grep -q '^cs35l43_dlkm ' /proc/modules; then
 echo 'bf3d042b681c119b0731123bee4477de26993e24c09f5e5e721ad76da98ebab3  '$M/cs35l43_dlkm.ko | $B sha256sum -c -
 echo AUDIO_MODULE_BEGIN=cs35l43_dlkm.ko
 $B timeout 12 $B insmod $M/cs35l43_dlkm.ko
 $B grep '^cs35l43_dlkm ' /proc/modules
fi
if ! $B grep -q '^wsa884x_dlkm ' /proc/modules; then
 echo '91fa7a0b7d55a82a93c7f4c9a22387297afba1e874d6cb1180f709d250d1ba6f  '$M/wsa884x_dlkm.ko | $B sha256sum -c -
 echo AUDIO_MODULE_BEGIN=wsa884x_dlkm.ko
 $B timeout 12 $B insmod $M/wsa884x_dlkm.ko
 $B grep '^wsa884x_dlkm ' /proc/modules
fi
if ! $B grep -q '^wsa883x_dlkm ' /proc/modules; then
 echo '0c554b62acafddabcc1a129ee83888dbe85c603b51f2bed7d0da830f5093c03e  '$M/wsa883x_dlkm.ko | $B sha256sum -c -
 echo AUDIO_MODULE_BEGIN=wsa883x_dlkm.ko
 $B timeout 12 $B insmod $M/wsa883x_dlkm.ko
 $B grep '^wsa883x_dlkm ' /proc/modules
fi
if ! $B grep -q '^lpass_cdc_rx_macro_dlkm ' /proc/modules; then
 echo '3d9ca510c0e4d3e6c558d3f7691b67180b3fc54674287dd1695e6c1e5d8794f3  '$M/lpass_cdc_rx_macro_dlkm.ko | $B sha256sum -c -
 echo AUDIO_MODULE_BEGIN=lpass_cdc_rx_macro_dlkm.ko
 $B timeout 12 $B insmod $M/lpass_cdc_rx_macro_dlkm.ko
 $B grep '^lpass_cdc_rx_macro_dlkm ' /proc/modules
fi
if ! $B grep -q '^audpkt_ion_dlkm ' /proc/modules; then
 echo 'b95ac3a195c0f3a0cac800b9e68c50bcb1591c9c4a5e7ca0ba98604b99311894  '$M/audpkt_ion_dlkm.ko | $B sha256sum -c -
 echo AUDIO_MODULE_BEGIN=audpkt_ion_dlkm.ko
 $B timeout 12 $B insmod $M/audpkt_ion_dlkm.ko
 $B grep '^audpkt_ion_dlkm ' /proc/modules
fi
if ! $B grep -q '^ucsi_glink ' /proc/modules; then
 echo '4ead755b90159370410c44288b03d5141bb31df2862818e1b947eab3388a8f9e  '$M/ucsi_glink.ko | $B sha256sum -c -
 echo AUDIO_MODULE_BEGIN=ucsi_glink.ko
 $B timeout 12 $B insmod $M/ucsi_glink.ko
 $B grep '^ucsi_glink ' /proc/modules
fi
if ! $B grep -q '^fsa4480_i2c ' /proc/modules; then
 echo '806b124086e9a7e986fe26321d4740dc64093fbdbd4537502f0246eba830c278  '$M/fsa4480-i2c.ko | $B sha256sum -c -
 echo AUDIO_MODULE_BEGIN=fsa4480-i2c.ko
 $B timeout 12 $B insmod $M/fsa4480-i2c.ko
 $B grep '^fsa4480_i2c ' /proc/modules
fi
if ! $B grep -q '^lpass_cdc_tx_macro_dlkm ' /proc/modules; then
 echo 'b5f2e32633b3f86a2573bcad6d9501c1d093c5bd58f39d2d38e753a66ab1da21  '$M/lpass_cdc_tx_macro_dlkm.ko | $B sha256sum -c -
 echo AUDIO_MODULE_BEGIN=lpass_cdc_tx_macro_dlkm.ko
 $B timeout 12 $B insmod $M/lpass_cdc_tx_macro_dlkm.ko
 $B grep '^lpass_cdc_tx_macro_dlkm ' /proc/modules
fi
if ! $B grep -q '^mbhc_dlkm ' /proc/modules; then
 echo 'b5dfb3ce445953af3c39a212557b5c9a4e352305d2c8e684af3af4ed86f9ddfe  '$M/mbhc_dlkm.ko | $B sha256sum -c -
 echo AUDIO_MODULE_BEGIN=mbhc_dlkm.ko
 $B timeout 12 $B insmod $M/mbhc_dlkm.ko
 $B grep '^mbhc_dlkm ' /proc/modules
fi
if ! $B grep -q '^audio_prm_dlkm ' /proc/modules; then
 echo 'f3a4b5f9d473b2f8d3b440d08c524bc20a735044765e7911efd904ed228a1ab4  '$M/audio_prm_dlkm.ko | $B sha256sum -c -
 echo AUDIO_MODULE_BEGIN=audio_prm_dlkm.ko
 $B timeout 12 $B insmod $M/audio_prm_dlkm.ko
 $B grep '^audio_prm_dlkm ' /proc/modules
fi
if ! $B grep -q '^wcd9xxx_dlkm ' /proc/modules; then
 echo 'e579b0f9ac290cfbba3229a967be0b57fb9da2c9dc8d3a28994e27e601f3f426  '$M/wcd9xxx_dlkm.ko | $B sha256sum -c -
 echo AUDIO_MODULE_BEGIN=wcd9xxx_dlkm.ko
 $B timeout 12 $B insmod $M/wcd9xxx_dlkm.ko
 $B grep '^wcd9xxx_dlkm ' /proc/modules
fi
if ! $B grep -q '^wcd938x_dlkm ' /proc/modules; then
 echo 'f41b106ae672260af03ece01a24cd351ea234488389de22440023ee970a39b13  '$M/wcd938x_dlkm.ko | $B sha256sum -c -
 echo AUDIO_MODULE_BEGIN=wcd938x_dlkm.ko
 $B timeout 12 $B insmod $M/wcd938x_dlkm.ko
 $B grep '^wcd938x_dlkm ' /proc/modules
fi
if ! $B grep -q '^machine_dlkm ' /proc/modules; then
 echo '3865de4fb52b65f145bfbb9092eb5bf38c61af0880463e34a26a866d1d0670e8  '$M/machine_dlkm.ko | $B sha256sum -c -
 echo AUDIO_MODULE_BEGIN=machine_dlkm.ko
 $B timeout 12 $B insmod $M/machine_dlkm.ko
 $B grep '^machine_dlkm ' /proc/modules
fi
echo AUDIO_CARD_COMPLETE=1
