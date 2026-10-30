set -eu
B=/busybox
T=/sys/kernel/tracing
I=$T/instances/sheng_meta_v129
P=/hmos-root/compat/lib64/libdisplay_buffer_vdi_impl.z.so
D=/hmos-root/data/local/tmp
[ "$($B sha256sum $P | $B cut -d ' ' -f1)" = 185e8d8e400f14d467c1f742f542225b1ad03dedb603f47f189f32edf6a28e24 ]
[ ! -d $T/events/sheng_v129 ]
[ ! -d $I ]
cleanup(){
 if [ -d $I ]; then
  echo 0 > $I/tracing_on
  echo 0 > $I/events/enable
  $B rmdir $I
 fi
 [ ! -d $T/events/sheng_v129/meta_ret ] || echo '-:sheng_v129/meta_ret' >> $T/uprobe_events
 [ ! -d $T/events/sheng_v129/meta ] || echo '-:sheng_v129/meta' >> $T/uprobe_events
 echo METADATA_TRACE_REMOVED
}
trap cleanup EXIT INT TERM
echo "p:sheng_v129/meta $P:0x2004 key=%x2:u32 fmt=+20(%x1):u32 width=+4(%x1):s32 height=+12(%x1):s32 begin=+0(%x3):x64 end=+8(%x3):x64" >> $T/uprobe_events
echo "r:sheng_v129/meta_ret $P:0x2004 ret=\$retval:s32" >> $T/uprobe_events
$B mkdir $I
echo 256 > $I/buffer_size_kb
echo mono > $I/trace_clock
echo 1 > $I/events/sheng_v129/enable
echo 1 > $I/tracing_on
$B sleep 2
echo 0 > $I/tracing_on
$B gzip -c $I/trace > $D/v129-metadata-uprobe.trace.gz
$B head -n 12 $I/trace
$B wc -c $D/v129-metadata-uprobe.trace.gz
