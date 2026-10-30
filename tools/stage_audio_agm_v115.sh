#!/busybox sh
# Reproduce the isolated original303 Bionic/AGM runtime in RAM. No playback.
set -eu
B=/busybox
D=/hmos-root/data/local/tmp
R=/compat/audio-runtime
P=/odm/etc/acdbdata/kalama_mtp

echo 'a22d693b394234833ca56519476b91ec367442e02ab9eb8e73ff53ad34138b35  '"$D/audio-bionic-v1.tar.gz" | $B sha256sum -c -
$B mkdir -p "$R"
$B tar -xzf "$D/audio-bionic-v1.tar.gz" -C "$R"
echo 'f9cea2822747f1437050621135d26b4630a67e6ba8370f1f8bb718a90ae2e2fc  '"$D/system-libcxx-303.so.gz" | $B sha256sum -c -
$B cp "$R/lib64/libc++.so" "$R/lib64/libc++_vndk33.so"
$B gunzip -c "$D/system-libcxx-303.so.gz" > "$R/lib64/libc++.so.new"
echo 'c6486cd3f0e6dd6a12346d3b1d55ef4bef7f1cc11e4a26bbe9da720c07d4b83b  '"$R/lib64/libc++.so.new" | $B sha256sum -c -
$B mv "$R/lib64/libc++.so.new" "$R/lib64/libc++.so"
echo 'ee83eb9147c33f4ec30f62972ac6df7e459b29b99c6210d0621b746f0f54ade3  '"$D/stock303-Forte-acdb.tar.xz" | $B sha256sum -c -
$B mkdir -p "$R/acdb/Forte"
$B tar -xJf "$D/stock303-Forte-acdb.tar.xz" -C "$R/acdb/Forte"
echo 'd9c2b9bf1281337bebfcaf498b2a9d12bd583f548a86bdf006cf5f8683bde6e4  '"$R/acdb/Forte/Forte_acdb_cal.acdb" | $B sha256sum -c -
echo '6836a92b70a1eb6169053ee1b0d9994d964c12de4976ac3d2b48f436f09d4e10  '"$R/acdb/Forte/Forte_workspaceFileXml.qwsp" | $B sha256sum -c -
[ ! -e /odm ] || exit 61
$B mkdir -p /odm/etc/acdbdata
$B ln -s "$R/acdb/Forte" "$P"
echo '77263f4b63cab0e989ea1a8afea5e16c5fa4b92b5005edbd4c07ae341b39c0ea  '"$D/libsheng_agm_probe.so" | $B sha256sum -c -
$B cp "$D/libsheng_agm_probe.so" "$R/lib64/"
[ ! -e /dev/aud_pasthru_adsp ] || exit 62
dev=$($B cat /sys/class/aud_pasthru_adsp/aud_pasthru_adsp/dev)
major=${dev%:*}
minor=${dev#*:}
[ "$major" != "$dev" ] || exit 63
$B mknod /dev/aud_pasthru_adsp c "$major" "$minor"
$B chmod 0600 /dev/aud_pasthru_adsp
echo AUDIO_AGM_RAM_RUNTIME_READY=1
