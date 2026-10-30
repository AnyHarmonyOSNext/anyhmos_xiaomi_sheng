#!/busybox sh
# Read-only argument/return tracing around the existing failed card probe.
# This does not unbind GPR, restart ADSP, or change a driver result.
set -eu
B=/busybox
T=/sys/kernel/debug/tracing
I=$T/instances/sheng_audio_v115
G=sheng_audio_v115
D=/hmos-root/data/local/tmp
[ -f "$T/kprobe_events" ] && [ ! -e "$I" ] || exit 30
[ ! -L /sys/bus/platform/devices/soc:spf_core_platform:sound/driver ] || exit 31
cleanup() {
    [ ! -e "$I/tracing_on" ] || echo 0 > "$I/tracing_on"
    [ ! -e "$I/events/$G/enable" ] || echo 0 > "$I/events/$G/enable"
    printf '%s\n' '-:sheng_audio_v115/runtime_enter' >> "$T/kprobe_events" 2>/dev/null || true
    printf '%s\n' '-:sheng_audio_v115/runtime_return' >> "$T/kprobe_events" 2>/dev/null || true
    $B rmdir "$I" 2>/dev/null || true
}
trap cleanup EXIT INT TERM
printf '%s\n' 'p:sheng_audio_v115/runtime_enter snd_soc_add_pcm_runtime link=+0(+0(%x1)):string codec=+0(+0(+32(%x1))):string dai=+0(+16(+32(%x1))):string node=+8(+32(%x1)):x64' >> "$T/kprobe_events"
printf '%s\n' 'r:sheng_audio_v115/runtime_return snd_soc_add_pcm_runtime result=$retval:s64' >> "$T/kprobe_events"
$B mkdir "$I"
echo 64 > "$I/buffer_size_kb"
echo 1 > "$I/events/$G/enable"
echo 1 > "$I/tracing_on"
echo soc:spf_core_platform:sound > /sys/bus/platform/drivers_probe || true
$B sleep 0.2
echo 0 > "$I/tracing_on"
$B cat "$I/trace" > "$D/v115-asoc-defer-trace.txt"
$B cat "$D/v115-asoc-defer-trace.txt"
echo ASOC_TRACE_DONE=1
