#!/busybox sh
set -eu
B=/busybox
S=/compat/audio-supplement-v1
[ "$($B cat /sys/module/firmware_class/parameters/path)" = /compat/firmware ] || exit 71
echo '8408b09ec8f45d012303d29a2a7978fd0bf5384435506e3baedbbf274d255169  '"$S/lib64/libagm_mixer_plugin.so" | $B sha256sum -c -
echo '651905db9117c81c609e1b1d7979fa04309603e076bf75d68e6fde584d0bde11  '"$S/lib64/libagm_pcm_plugin.so" | $B sha256sum -c -
echo '52f2a46cdd795486c04b876738a14f6a3a06d9878efb7b1b1694fd78de994477  '"$S/lib64/libagm_compress_plugin.so" | $B sha256sum -c -
echo '371232bb8e7984994288c6cd16c6c5cca1dceca9d60ef6f2d6ec43ccdb6fa750  '"$S/lib64/libsndcardparser.so" | $B sha256sum -c -
echo '081e667cbbdcb52cf418006277945ed2d2038a26a569d84c687d34e495668605  '"$S/lib64/libbacktrace.so" | $B sha256sum -c -
echo '97c35429427e17ded24643b3fdc410b6e53ba7884358ad805074a4ec35ad8f2a  '"$S/config/vendor/etc/card-defs.xml" | $B sha256sum -c -
echo 'b403ea5687ccd8c00f8aea29bd688cabcf31175fdd6feb7efa44cc2d64204aa4  '"$S/config/vendor/etc/kvh2xml.xml" | $B sha256sum -c -
echo 'd2b68e8bca92e97cd4e9af9af8689166af9a3a0974a524c41b104dca02cbb513  '"$S/config/vendor/etc/usecaseKvManager.xml" | $B sha256sum -c -
echo '4640cf56a2a5fdef04072ccb5e69dbfecde319368c14ad1d8c3493887426dbcc  '"$S/config/odm/etc/usecaseKvManager.xml" | $B sha256sum -c -
echo '1535aedfff5a344939e2b676cd735be2eea44a6a8ac2f5e6eef5aa32e88aacfc  '"$S/config/odm/etc/audio/sku_kalama/mixer_paths_kalama_mtp.xml" | $B sha256sum -c -
echo 'e674891e7dd4bde5195620528445c36c8b0fb69daedf6a8069ed94c7c9484e03  '"$S/config/odm/etc/audio/sku_kalama/mixer_paths_overlay_dynamic.xml" | $B sha256sum -c -
echo 'a663f9ae572ded046b5eb0da15273e110f6c1bfd7a4fc9c4b8572a169b999409  '"$S/config/odm/etc/audio/sku_kalama/mixer_paths_overlay_static.xml" | $B sha256sum -c -
echo 'dabb48abf7841ad511881195a334496bbe406451b61636e8ff652a70d12ce83f  '"$S/config/odm/etc/audio/sku_kalama/resourcemanager_kalama_mtp.xml" | $B sha256sum -c -
echo '0f4e2138b94364d051995bc0abaadc2e5a468eb7dc48933c5bad9a30f06f4af0  '"$S/firmware/BLH-cs35l43-dsp1-spk-prot.bin" | $B sha256sum -c -
echo 'cfc9ce1678e290ab39cede51fa9aa0ea1b370bdf2f5604c79581419137f46a97  '"$S/firmware/BLL-cs35l43-dsp1-spk-prot.bin" | $B sha256sum -c -
echo 'ffb24e16da20e0c63c0c94c9f2986e32ca5d99e5537033b1061fb70779b4b63b  '"$S/firmware/BRL-cs35l43-dsp1-spk-prot.bin" | $B sha256sum -c -
echo 'bcddaf83e276b49815eeed283e8aacdd30a819447122a27d118445c5c97d21e7  '"$S/firmware/cs35l43-dsp1-spk-prot.wmfw" | $B sha256sum -c -
echo '50cef4822bcbc1047a1634e7abb96dce37d5e03cd8e0de241c0f477c06b808d3  '"$S/firmware/TLH-cs35l43-dsp1-spk-prot.bin" | $B sha256sum -c -
echo '2365b66dbaeb8063403ac5e70b795cbd4822e4842552a2de6ef96f59f96459e1  '"$S/firmware/TLL-cs35l43-dsp1-spk-prot.bin" | $B sha256sum -c -
echo '3f3f6696438bc51cf9a1f288efc9f352f94ab9a6993f00ddddfe7554428deeb0  '"$S/firmware/TRL-cs35l43-dsp1-spk-prot.bin" | $B sha256sum -c -
for src in "$S"/firmware/*; do
 name=${src##*/}
 [ ! -e "/compat/firmware/$name" ] || {
   a=$($B sha256sum "$src"); a=${a%% *}
   b=$($B sha256sum "/compat/firmware/$name"); b=${b%% *}
   [ "$a" = "$b" ] || exit 72
 }
 $B cp "$src" "/compat/firmware/$name"
done
echo AUDIO_ORIGINAL_SUPPLEMENT_READY=1
