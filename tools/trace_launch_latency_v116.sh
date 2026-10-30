#!/busybox sh
# Bounded diagnostic capture. Restore every global trace control on exit.
set -eu
B=/busybox
R=/hmos-root
T=/sys/kernel/tracing
I=$T/instances/sheng_latency
D=$R/data/local/tmp
P=$D/latency-v116-injected-${1:-2225}
[ "$(cat "$T/current_tracer")" = nop ] || exit 31
[ "$(cat "$T/events/enable")" = 0 ] || exit 32
old_on=$(cat "$T/tracing_on")
old_size=$(cat "$T/buffer_size_kb")
old_clock=$($B sed -n 's/.*\[\([^]]*\)\].*/\1/p' "$T/trace_clock")
old_marker_mode=$($B stat -c %a "$T/trace_marker")
old_tags=$($B chroot "$R" /system/bin/param get debug.hitrace.tags.enableflags | $B tr -d ' \r\n')
cleanup() {
  $B chroot "$R" /system/bin/param set debug.hitrace.tags.enableflags "$old_tags" || true
  $B chmod "$old_marker_mode" "$T/trace_marker"
  echo 0 > "$T/tracing_on"
  echo 0 > "$I/tracing_on"
  echo 0 > "$I/events/sched/enable"
  echo "$old_size" > "$T/buffer_size_kb"
  echo "$old_clock" > "$T/trace_clock"
  echo "$old_on" > "$T/tracing_on"
  echo "TRACE_RESTORED tags=$old_tags buffer=$old_size clock=$old_clock on=$old_on marker_mode=$old_marker_mode"
}
trap cleanup EXIT INT TERM
echo 0 > "$T/tracing_on"
$B gzip -c "$T/trace" > "$P-prior.trace.gz"
echo 4096 > "$T/buffer_size_kb"
echo mono > "$T/trace_clock"
echo > "$T/trace"
echo > "$I/trace"
echo 1 > "$I/events/sched/sched_switch/enable"
echo 1 > "$I/events/sched/sched_waking/enable"
echo 1 > "$I/tracing_on"
$B chmod 0222 "$T/trace_marker"
$B chroot "$R" /system/bin/param set debug.hitrace.tags.enableflags 4611761611999281152
echo 1 > "$T/tracing_on"
echo TRACE_READY=1
cat /proc/uptime
$B sleep 45
echo 0 > "$T/tracing_on"
echo 0 > "$I/tracing_on"
$B gzip -c "$T/trace" > "$P-userspace.trace.gz"
$B gzip -c "$I/trace" > "$P-sched.trace.gz"
echo TRACE_SAVED=1
$B wc -c "$P-userspace.trace.gz" "$P-sched.trace.gz"
