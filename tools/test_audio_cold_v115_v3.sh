#!/busybox sh
# Bounded runtime trial only. Never rebind a live GPR/rpmsg channel.
set -eu
B=/busybox
D=/hmos-root/data/local/tmp
S=/compat/original-firmware/image
M=/compat/pd-maps
P=$D/sheng-pd-mapper-v1
[ "$($B uname -r)" = 5.15.178-android13-8-00021-g6f2f96be86b9-ab13729987 ] || exit 30
boot_id=$($B cat /proc/sys/kernel/random/boot_id)
wifi_log=$D/v115-wifi-startup.log
[ "$($B head -1 "$wifi_log")" = "$boot_id" ] || exit 46
$B grep -q '^WIFI_START_EXIT=0 STAGE=complete$' "$wifi_log" || exit 47
[ -e /sys/class/net/wlan0 ] || exit 48
uptime=$($B awk '{print int($1)}' /proc/uptime)
[ "$uptime" -ge 210 ] || exit 49
$B grep -q '^/dev/block/sde7 /compat/original-firmware vfat ro,' /proc/mounts || exit 50
echo WIFI_READY_BEFORE_AUDIO=1
$B grep -q 'no soundcards' /proc/asound/cards || exit 31
[ ! -e /sys/class/remoteproc/remoteproc0/state ] || {
    [ "$($B cat /sys/class/remoteproc/remoteproc0/state)" = offline ] || exit 32
}
echo '761fb42c0c3f92f58189eccd11e75f11653b77f2394b15a4059b05a34355a38f  '"$P" | $B sha256sum -c -
echo "$boot_id"
$B mount -t debugfs debugfs /sys/kernel/debug 2>/dev/null || true
$B sh "$D/stage-audio-firmware-v115.sh" > "$D/v115-cold-audio-firmware.txt" 2>&1
$B tail -1 "$D/v115-cold-audio-firmware.txt"
for stage in qrtr-smd qcom_q6v5_pas smp2p audio-transport audio-card; do
    $B sh "$D/load-official303-$stage.sh" > "$D/v115-cold-$stage.txt" 2>&1
    $B tail -1 "$D/v115-cold-$stage.txt"
done
# The stock audio-pkt platform driver registers its GPR driver before it
# initializes ap_priv->status. Loading it after the GPR child exists resets
# the status to INIT after probe. Register now, before booting ADSP.
[ ! -e /sys/bus/gprbus/devices/gprsvc:audio-pkt:2:17 ] || exit 37
$B sh "$D/load-official303-audio_pkt_dlkm.sh" > "$D/v115-cold-audio-pkt-v3.txt" 2>&1
$B tail -1 "$D/v115-cold-audio-pkt-v3.txt"
[ -d /sys/bus/gprbus/drivers/audio-pkt ] || exit 38
echo AUDIO_PKT_LOADED_BEFORE_GPR=1
$B sh "$D/load-official303-wcd938x_slave_dlkm.sh" > "$D/v115-cold-wcd-v3.txt" 2>&1
$B sh "$D/load-official303-bt_fm_slim.sh" > "$D/v115-cold-btfm-v3.txt" 2>&1
$B sh "$D/load-official303-slim-qcom-ngd-ctrl.sh" > "$D/v115-cold-slim-v3.txt" 2>&1
echo SLIM_LOADED_BEFORE_ADSP=1
[ "$($B cat /sys/class/remoteproc/remoteproc0/name)" = 3000000.remoteproc-adsp ] || exit 33
[ "$($B cat /sys/class/remoteproc/remoteproc0/state)" = offline ] || exit 34
$B mkdir -p "$M"
for src in "$S"/*.jsn; do
    name=${src##*/}
    $B cp "$src" "$M/$name"
    a=$($B sha256sum "$src"); a=${a%% *}
    b=$($B sha256sum "$M/$name"); b=${b%% *}
    [ "$a" = "$b" ] || exit 35
    echo "PD_COLD_DESCRIPTOR_SHA=$a:$name"
done
"$P" --maps-dir "$M" --validate > "$D/v115-cold-pd-validate.txt" 2>&1
$B tail -1 "$D/v115-cold-pd-validate.txt"
log=$D/v115-cold-pd-mapper-v3.txt
$B setsid $B timeout 1200 "$P" --maps-dir "$M" > "$log" 2>&1 < /dev/null &
pid=$!
echo "$pid" > "$D/v115-cold-pd-mapper.pid"
echo "PD_COLD_MAPPER_PID=$pid"
i=0
while ! $B grep -q '^PD_LOCATOR_PUBLISHED=64:257:0$' "$log"; do
    [ -d /proc/"$pid" ] && [ "$i" -lt 20 ] || exit 36
    $B sleep 0.1
    i=$((i+1))
done
$B cat /proc/sys/kernel/printk > "$D/v115-cold-before-printk.txt"
$B dmesg -n 1
echo PD_COLD_LOCATOR_READY_BEFORE_DSP=1
echo 1 > /sys/kernel/boot_adsp/boot
$B sleep 2
$B cat /sys/class/remoteproc/remoteproc0/state
attempt=0
while $B grep -q 'no soundcards' /proc/asound/cards; do
    [ "$attempt" -lt 50 ] || exit 51
    $B sleep 0.1
    attempt=$((attempt+1))
done
$B cat /proc/asound/cards
[ -e /sys/bus/gprbus/devices/gprsvc:audio-pkt:2:17/driver ] || exit 39
echo AUDIO_COLD_V3_TRIAL_STARTED=1
