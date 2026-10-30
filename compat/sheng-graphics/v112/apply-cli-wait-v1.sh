#!/busybox sh
set -eu
B=/busybox
R=/hmos-root
S=$R/system/lib64/platformsdk/libcli_tool_client.z.so
T=$R/compat/lib64/libcli_tool_client.z.so
sum=$($B sha256sum "$S"); sum=${sum%% *}
if [ "$sum" = 270f676dd0e500f91ff4bd34b866c2d12ae9f4731f0228f874ace26228678974 ]; then echo CLI_WAIT_ALREADY_STAGED=1; exit 0; fi
[ "$sum" = 729f4999e99d6dc9eb83eceda08dc9e68a4369ab8e057d450c8d5f7448b64910 ] || exit 62
$B cp "$S" "$T"
$B printf '\010\040\234\122' | $B dd of="$T" bs=1 seek=142880 conv=notrunc 2>/dev/null
$B printf '\250\276\240\162' | $B dd of="$T" bs=1 seek=142892 conv=notrunc 2>/dev/null
echo '270f676dd0e500f91ff4bd34b866c2d12ae9f4731f0228f874ace26228678974  '"$T" | $B sha256sum -c -
$B chmod 0644 "$T"
$B mount --bind "$T" "$S"
echo OPTIONAL_CLI_WAIT_BUDGET_100MS_STAGED=1
