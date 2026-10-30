#!/busybox sh
# Guarded RAM overlay. The system image and vendor remain unchanged.
set -eu
B=/busybox
R=/hmos-root
S=$R/system/lib64/libtime_system_ability.z.so
T=$R/compat/lib64/libtime_system_ability.z.so
sum=$($B sha256sum "$S"); sum=${sum%% *}
if [ "$sum" = 9d3343de0b2557cca3c7747c5009cde8d5e56597adf5784e8f6b77245e2d0b7d ]; then echo TIME_TIMERFDS_RAM_ALREADY_STAGED=1; exit 0; fi
[ "$sum" = aa5383b1cb0201e4b5b87850c80f33bd3e82efda9165d9b0ea122a4618152cf4 ] || exit 61
$B cp "$S" "$T"
$B printf '\000\000\200\022\140\172\064\270\072\000\000\024' | $B dd of="$T" bs=1 seek=241392 conv=notrunc 2>/dev/null
echo '9d3343de0b2557cca3c7747c5009cde8d5e56597adf5784e8f6b77245e2d0b7d  '"$T" | $B sha256sum -c -
$B chmod 0644 "$T"
$B mount --bind "$T" "$S"
echo '9d3343de0b2557cca3c7747c5009cde8d5e56597adf5784e8f6b77245e2d0b7d  '"$S" | $B sha256sum -c -
echo TIME_TIMERFDS_RAM_STAGED_SIX_REAL_CLOCKS=1
