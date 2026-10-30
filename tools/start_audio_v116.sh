#!/busybox sh
# Real original303 DSP boot, PAL backend and original native service identity.
set -eu
B=/busybox
R=/hmos-root
D=$R/data/local/tmp
S=/compat/audio/scripts
P=/compat/audio-pal-v1
stage=check
trap 'rc=$?; echo "AUDIO_START_EXIT=$rc STAGE=$stage"' EXIT
[ -f /sheng-audio-v1/SHA256SUMS ] || exit 21
[ "$($B uname -r)" = 5.15.178-android13-8-00021-g6f2f96be86b9-ab13729987 ] || exit 22
boot_id=$($B cat /proc/sys/kernel/random/boot_id)
[ "$($B head -1 "$D/v116-wifi-startup.log")" = "$boot_id" ] || exit 23
$B grep -q '^WIFI_START_EXIT=0 STAGE=complete$' "$D/v116-wifi-startup.log"
[ -e /sys/class/net/wlan0 ]
$B grep -q 'no soundcards' /proc/asound/cards
stage=firmware
$B sh "$S/stage-audio-firmware.sh"
for name in qrtr-smd qcom_q6v5_pas smp2p audio-transport audio-card; do
 stage=$name
 $B sh "$S/load-official303-$name.sh"
done
stage=audio-pkt-before-adsp
[ ! -e /sys/bus/gprbus/devices/gprsvc:audio-pkt:2:17 ]
$B sh "$S/load-official303-audio_pkt_dlkm.sh"
for name in wcd938x_slave_dlkm bt_fm_slim slim-qcom-ngd-ctrl; do
 stage=$name
 $B sh "$S/load-official303-$name.sh"
done
stage=pd-locator
[ "$($B cat /sys/class/remoteproc/remoteproc0/name)" = 3000000.remoteproc-adsp ]
[ "$($B cat /sys/class/remoteproc/remoteproc0/state)" = offline ]
$B mkdir -p /compat/pd-maps
$B cp /compat/original-firmware/image/*.jsn /compat/pd-maps/
/compat/audio/bin/sheng-pd-mapper --maps-dir /compat/pd-maps --validate
$B setsid /compat/audio/bin/sheng-pd-mapper --maps-dir /compat/pd-maps > "$D/v116-pd-mapper.txt" 2>&1 </dev/null &
p=$!; echo "$p" > "$D/v116-pd-mapper.pid"
i=0
while ! $B grep -q '^PD_LOCATOR_PUBLISHED=64:257:0$' "$D/v116-pd-mapper.txt"; do
 [ -d /proc/$p ] && [ "$i" -lt 30 ] || exit 24
 i=$((i+1)); $B sleep 0.1
done
stage=adsp
echo 1 > /sys/kernel/boot_adsp/boot
i=0
while $B grep -q 'no soundcards' /proc/asound/cards; do
 [ "$i" -lt 100 ] || exit 25
 i=$((i+1)); $B sleep 0.1
done
[ "$($B cat /sys/class/remoteproc/remoteproc0/state)" = running ]
[ -e /sys/bus/gprbus/devices/gprsvc:audio-pkt:2:17/driver ]
$B sh "$S/stage-audio-nodes.sh"
$B sh "$S/stage-audio-supplement.sh"
stage=pal
[ -z "$($B grep sheng.pal.pcm /proc/net/unix)" ]
A=/compat/audio-runtime
U=/compat/audio-supplement-v1
LD_LIBRARY_PATH=$A/lib64:$U/lib64:$P/lib64 LD_PRELOAD=$P/libsheng_pal_lifecycle_clean.so:$P/libsheng_audio_paths.so:$P/libsheng_pal_server_v1c.so:$A/lib64/libagm.so $B setsid $A/bin/linker64 $A/bin/agmplay -h > "$D/v116-pal-server.txt" 2>&1 </dev/null &
p=$!; echo "$p" > "$D/v116-pal-server.pid"
i=0
while ! $B grep -q '^PAL_SERVER_READY=1 ' "$D/v116-pal-server.txt"; do
 [ -d /proc/$p ] && [ "$i" -lt 100 ] || exit 26
 i=$((i+1)); $B sleep 0.1
done
stage=native
$B chroot "$R" /system/bin/param set sheng.debug.start.audio true
stage=complete
