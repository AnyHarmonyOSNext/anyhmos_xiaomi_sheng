#!/busybox sh
set -eu
B=/busybox
R=/hmos-root
S=$R/system/lib64/libmemmgrservice.z.so
T=$R/compat/lib64/libmemmgrservice.z.so
sum=$($B sha256sum "$S"); sum=${sum%% *}
if [ "$sum" = 955766ec18af6004bc3964fac84e732c80978631c61a68a78421bf9f456164c2 ]; then echo MEMMGR_NATIVE_PORT_ALREADY_STAGED=1; exit 0; fi
[ "$sum" = 8083924f66b8f3888f39b6bd400d8afbd5f21d6c02f24e553c01dcc208fc185d ] || exit 62
$B cp "$S" "$T"
$B printf '\003\000\000\024' | $B dd of="$T" bs=1 seek=1675120 conv=notrunc 2>/dev/null
echo '955766ec18af6004bc3964fac84e732c80978631c61a68a78421bf9f456164c2  '"$T" | $B sha256sum -c -
$B chmod 0644 "$T"
$B mount --bind "$T" "$S"
echo '955766ec18af6004bc3964fac84e732c80978631c61a68a78421bf9f456164c2  '"$S" | $B sha256sum -c -
echo MEMMGR_NATIVE_PORT_STAGED_UNSUPPORTED_HYPERHOLD_DISABLED=1
