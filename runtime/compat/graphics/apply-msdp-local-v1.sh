#!/busybox sh
set -eu
/busybox sh /graphics/apply-storage-local-v1.sh
B=/busybox
R=/hmos-root
S=$R/system/lib64/libdevicestatus_service.z.so
T=$R/compat/lib64/libdevicestatus_service.z.so
sum=$($B sha256sum "$S"); sum=${sum%% *}
if [ "$sum" = d02d06d53651f409268ae6e4320de0d85349a875bd91d94950f5c4cbda3b15d3 ]; then echo MSDP_LOCAL_ALREADY_STAGED=1; exit 0; fi
[ "$sum" = 483742fb4249e79319565814dab375b3db0ddd71de9995f99b5e254b3b2dfd69 ] || exit 62
$B cp "$S" "$T"
$B printf '\037\040\003\325' | $B dd of="$T" bs=1 seek=519904 conv=notrunc 2>/dev/null
$B printf '\037\040\003\325' | $B dd of="$T" bs=1 seek=519924 conv=notrunc 2>/dev/null
echo "d02d06d53651f409268ae6e4320de0d85349a875bd91d94950f5c4cbda3b15d3  $T" | $B sha256sum -c -
$B chmod 0644 "$T"
$B mount --bind "$T" "$S"
echo "d02d06d53651f409268ae6e4320de0d85349a875bd91d94950f5c4cbda3b15d3  $S" | $B sha256sum -c -
echo MSDP_LOCAL_NATIVE_IPC_STAGED_OPTIONAL_DISTRIBUTED_STARTUP_DISABLED=1
