#!/busybox sh
set -eu
B=/busybox
R=/hmos-root
$B mkdir -p "$R/compat/lib64"
$B cp /graphics/libdbkeys.so "$R/compat/lib64/libdbkeys.so"
echo "eb0c3a10b9cc1f468341d1e7cc8293d829bd795e108d39379a1919ff9cbeca8a  $R/compat/lib64/libdbkeys.so" | $B sha256sum -c -
$B chmod 0644 "$R/compat/lib64/libdbkeys.so"
$B mkdir -p "$R/data/service/el1/public/database/.sheng-dbkeys"
$B chown 0:0 "$R/data/service/el1/public/database/.sheng-dbkeys"
$B chmod 0711 "$R/data/service/el1/public/database/.sheng-dbkeys"
# Native UIDs get private directories before services start; apps use their own sandbox.
while IFS=: read -r name pass uid gid rest; do
 case "$uid" in ""|*[!0-9]*) continue;; esac
 [ "$uid" -lt 10000 ] || continue
 P="$R/data/service/el1/public/database/.sheng-dbkeys/$uid"
 $B mkdir -p "$P"; $B chown "$uid:$gid" "$P"; $B chmod 0700 "$P"
done < "$R/system/etc/passwd"
S="$R/system/lib64/librelational_store_crypt.z.so"
T="$R/compat/lib64/librelational_store_crypt.z.so"
sum=$($B sha256sum "$S"); sum=${sum%% *}
if [ "$sum" != efb3ac93f32b3c48ec4145b375888809cc02da27e3e0217b0e7a731ee1e7429d ]; then
 [ "$sum" = de22d9087b4b4eb2c4802f5987128cff11d9e3ff4692f619dd0e64df96577131 ] || exit 65
$B cp "$S" "$T"
 $B printf '\154\151\142\144\142\153\145\171\163\056\163\157\000\000\000\000' | $B dd of="$T" bs=1 seek=3615 conv=notrunc 2>/dev/null
 $B printf '\123\153\163\107\145\156\145\162\141\164\145\122\141\156\144\157\155\000' | $B dd of="$T" bs=1 seek=3171 conv=notrunc 2>/dev/null
 $B printf '\123\153\163\107\145\156\145\162\141\164\145\113\145\171\000' | $B dd of="$T" bs=1 seek=3074 conv=notrunc 2>/dev/null
 $B printf '\123\153\163\113\145\171\105\170\151\163\164\000' | $B dd of="$T" bs=1 seek=3089 conv=notrunc 2>/dev/null
 $B printf '\123\153\163\111\156\151\164\000' | $B dd of="$T" bs=1 seek=3004 conv=notrunc 2>/dev/null
 $B printf '\123\153\163\125\160\144\141\164\145\000' | $B dd of="$T" bs=1 seek=2928 conv=notrunc 2>/dev/null
 $B printf '\123\153\163\106\151\156\151\163\150\000' | $B dd of="$T" bs=1 seek=2994 conv=notrunc 2>/dev/null
 $B printf '\123\153\163\101\142\157\162\164\000' | $B dd of="$T" bs=1 seek=2919 conv=notrunc 2>/dev/null
 echo "efb3ac93f32b3c48ec4145b375888809cc02da27e3e0217b0e7a731ee1e7429d  $T" | $B sha256sum -c -
 $B chmod 0644 "$T"; $B mount --bind "$T" "$S"
fi
S="$R/system/lib64/libkv_store_crypt.z.so"
T="$R/compat/lib64/libkv_store_crypt.z.so"
sum=$($B sha256sum "$S"); sum=${sum%% *}
if [ "$sum" != c8ca6133b81e090c8342e85d6a7e15e820f8e4b226e4d44b94b17be660447eab ]; then
 [ "$sum" = 1c2520958efe51b55a4fa3eb50ea740135dddc75499e0046d4861d97a6e86421 ] || exit 65
$B cp "$S" "$T"
 $B printf '\154\151\142\144\142\153\145\171\163\056\163\157\000\000\000\000' | $B dd of="$T" bs=1 seek=2723 conv=notrunc 2>/dev/null
 $B printf '\123\153\163\107\145\156\145\162\141\164\145\122\141\156\144\157\155\000' | $B dd of="$T" bs=1 seek=2204 conv=notrunc 2>/dev/null
 $B printf '\123\153\163\107\145\156\145\162\141\164\145\113\145\171\000' | $B dd of="$T" bs=1 seek=2318 conv=notrunc 2>/dev/null
 $B printf '\123\153\163\113\145\171\105\170\151\163\164\000' | $B dd of="$T" bs=1 seek=2333 conv=notrunc 2>/dev/null
 $B printf '\123\153\163\105\156\143\162\171\160\164\000' | $B dd of="$T" bs=1 seek=2345 conv=notrunc 2>/dev/null
 $B printf '\123\153\163\104\145\143\162\171\160\164\000' | $B dd of="$T" bs=1 seek=2356 conv=notrunc 2>/dev/null
 echo "c8ca6133b81e090c8342e85d6a7e15e820f8e4b226e4d44b94b17be660447eab  $T" | $B sha256sum -c -
 $B chmod 0644 "$T"; $B mount --bind "$T" "$S"
fi
echo DB_KEY_WRAPPING_SOFTWARE_AES256_GCM_STAGED=1
