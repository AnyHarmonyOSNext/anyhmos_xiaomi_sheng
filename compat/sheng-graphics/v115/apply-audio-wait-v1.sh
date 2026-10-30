#!/busybox sh
set -eu
B=/busybox
R=/hmos-root
S=$R/system/lib64/libaudio_policy_service.z.so
T=$R/compat/lib64/libaudio_policy_service.z.so
sum=$($B sha256sum "$S"); sum=${sum%% *}
if [ "$sum" = 8d630c3df884396d56a6bd9ca6ea2937b904f5f18dc33f76de3ed05646e34518 ]; then echo AUDIO_WAIT_ALREADY_STAGED=1; exit 0; fi
[ "$sum" = a861efe809d18e8f2a5586d7834e649982477f57a4731696f7185fe63f725844 ] || exit 62
$B cp "$S" "$T"
$B printf '\126\000\200\122' | $B dd of="$T" bs=1 seek=3240312 conv=notrunc 2>/dev/null
echo '8d630c3df884396d56a6bd9ca6ea2937b904f5f18dc33f76de3ed05646e34518  '"$T" | $B sha256sum -c -
$B chmod 0644 "$T"
$B mount --bind "$T" "$S"
echo AUDIO_VOLUME_GROUP_WAIT_400MS_STAGED=1
