#!/busybox sh
# Create RAM device nodes using the current kernel's sysfs numbers only.
set -eu
B=/busybox
node() {
    src=$1
    dst=$2
    [ -f "$src/dev" ] || exit 64
    dev=$($B cat "$src/dev")
    major=${dev%:*}
    minor=${dev#*:}
    case "$major:$minor" in *[!0-9:]*|:*) exit 65;; esac
    [ "$major" != "$dev" ] && [ -n "$minor" ] || exit 66
    [ ! -L "$dst" ] || exit 67
    if [ -e "$dst" ]; then
        [ -c "$dst" ] || exit 68
        hexmajor=$($B stat -c %t "$dst")
        hexminor=$($B stat -c %T "$dst")
        [ "$((0x$hexmajor))" -eq "$major" ] && [ "$((0x$hexminor))" -eq "$minor" ] || exit 69
    else
        $B mknod "$dst" c "$major" "$minor"
        $B chmod 0600 "$dst"
    fi
    echo "AUDIO_NODE=$dst:$dev"
}
$B mkdir -p /dev/snd /dev/dma_heap
node /sys/class/aud_pasthru_adsp/aud_pasthru_adsp /dev/aud_pasthru_adsp
node /sys/class/dma_heap/system /dev/dma_heap/system
node /sys/class/msm_audio_ion/msm_audio_ion /dev/msm_audio_ion
node /sys/class/msm_audio_ion_cma/msm_audio_ion_cma /dev/msm_audio_ion_cma
for src in /sys/class/sound/*; do
    name=${src##*/}
    case "$name" in
        controlC[0-9]*|pcmC[0-9]*|comprC[0-9]*|hwC[0-9]*|timer|seq)
            node "$src" "/dev/snd/$name";;
    esac
done
[ -c /dev/snd/controlC0 ] || exit 70
echo AUDIO_RAM_NODES_READY=1
