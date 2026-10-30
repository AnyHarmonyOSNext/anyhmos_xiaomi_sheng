#!/busybox sh
# Bounded runtime trial only. Never rebind a live GPR/rpmsg channel.
set -eu
B=/busybox
D=/hmos-root/data/local/tmp
S=/compat/original-firmware/image
M=/compat/pd-maps
P=$D/sheng-pd-mapper-v1
[ "$($B uname -r)" = 5.15.178-android13-8-00021-g6f2f96be86b9-ab13729987 ] || exit 30
$B grep -q 'no soundcards' /proc/asound/cards || exit 31
[ ! -e /sys/class/remoteproc/remoteproc0/state ] || {
    [ "$($B cat /sys/class/remoteproc/remoteproc0/state)" = offline ] || exit 32
}
echo '761fb42c0c3f92f58189eccd11e75f11653b77f2394b15a4059b05a34355a38f  '"$P" | $B sha256sum -c -
$B cat /proc/sys/kernel/random/boot_id
$B mount -t debugfs debugfs /sys/kernel/debug 2>/dev/null || true
$B sh "$D/stage-audio-firmware-v115.sh" > "$D/v115-cold-audio-firmware.txt" 2>&1
$B tail -1 "$D/v115-cold-audio-firmware.txt"
for stage in qrtr-smd qcom_q6v5_pas smp2p audio-transport audio-card; do
    $B sh "$D/load-official303-$stage.sh" > "$D/v115-cold-$stage.txt" 2>&1
    $B tail -1 "$D/v115-cold-$stage.txt"
done
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
log=$D/v115-cold-pd-mapper.txt
$B setsid $B timeout 300 "$P" --maps-dir "$M" > "$log" 2>&1 < /dev/null &
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
$B cat /proc/asound/cards
echo AUDIO_COLD_TRIAL_STARTED=1
