#!/busybox sh
# Called in the outer bootstrap namespace, after whole userdata mount.
set -eu
B=/busybox
R=/hmos-root
P=/sheng-audio-v1
[ -f "$P/SHA256SUMS" ] || { echo AUDIO_PAYLOAD_ABSENT_DESKTOP_CONTINUES; exit 0; }
cd "$P"
$B sha256sum -c SHA256SUMS > "$R/data/local/tmp/v116-audio-payload-check.txt"
$B mkdir -p /compat "$R/compat/bin" "$R/compat/lib64" "$R/compat/etc/audio" "$R/chip_prod/etc" /odm/etc/acdbdata
for name in audio-runtime audio-pal-v1 audio-supplement-v1 audio; do
 [ ! -e "/compat/$name" ]
 $B ln -s "$P/$name" "/compat/$name"
done
$B ln -s /compat/audio-runtime/acdb/Forte /odm/etc/acdbdata/kalama_mtp
$B cp "$P"/audio/native/lib64/* "$R/compat/lib64/"
$B cp "$P"/audio/native/bin/* "$R/compat/bin/"
$B chmod 0755 "$R"/compat/bin/native_audio_* "$R/compat/bin/native_system_audio_check"
$B cp -R "$P/audio/policy/audio/." "$R/compat/etc/audio/"
[ ! -e "$R/chip_prod/etc/audio" ]
$B ln -s /compat/etc/audio "$R/chip_prod/etc/audio"
: > "$R/data/local/tmp/sheng-audio-server.txt"
: > "$R/data/local/tmp/sheng-audio-host.txt"
$B chown 1041:1000 "$R/data/local/tmp/sheng-audio-server.txt"
$B chown 3127:3127 "$R/data/local/tmp/sheng-audio-host.txt"
$B chmod 0600 "$R/data/local/tmp/sheng-audio-server.txt" "$R/data/local/tmp/sheng-audio-host.txt"
echo AUDIO_PERSISTENT_PAYLOAD_STAGED=1
