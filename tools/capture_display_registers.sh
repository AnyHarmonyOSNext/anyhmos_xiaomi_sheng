#!/system/bin/sh
# Read selected display registers through the vendor driver's debugfs reader.
# sde_off selects a read range only. This script never writes sde_reg/MMIO.
set -u
export TMPDIR=/tmp
p=/sys/kernel/debug/dri/0/debug
echo DISPLAY_SNAPSHOT_BEGIN
uname -r
for f in /sys/kernel/debug/dri/0/crtc176/status /sys/kernel/debug/dri/0/crtc176/state /sys/kernel/debug/dri/0/encoder64/status; do
    echo FILE=$f
    cat "$f"
done
while read offset length; do
    echo DISPLAY_REGISTER=$offset,$length
    if echo "$offset $length" >"$p/sde_off"; then
        cat "$p/sde_reg"
    else
        echo RANGE_UNAVAILABLE
    fi
done <<'RANGES'
0 5c
16000 100
16100 100
16200 90
45000 100
46000 100
6a000 4
6b000 4
36000 100
36100 100
36200 100
37000 100
37100 100
37200 100
81000 4
81100 9c
81200 9c
81f00 24
81f80 24
82000 4
RANGES
echo '0 5c' >"$p/sde_off"
echo DISPLAY_SNAPSHOT_END
